"""
EC Language Lab — Real-Database Adversarial Security Test Suite
Runs against a real temporary SQLite database (no mocks) via Flask's test client.
Covers all 4 Security Pillars:
  1. Server-Side Privileged Operations, Rate Limiting, CSRF, Security Headers & Zero Hardcoded Secrets
  2. Private Storage Path Containment & Binary Magic-Byte File Validation
  3. Privacy & Data Minimization (Zero password_hash / Raw Email Leakage)
  4. Real-Database IDOR, Privilege Escalation, SQLi & Immediate Session Revocation
"""

import io
import os
import re
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure an isolated temporary data directory & real SQLite database BEFORE importing app
_TMP_DIR = tempfile.TemporaryDirectory(prefix='ec_sec_test_')
os.environ['DATA_DIR'] = _TMP_DIR.name
os.environ['DATABASE_PATH'] = os.path.join(_TMP_DIR.name, 'sec_test.db')
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['ADMIN_PASSWORD'] = 'TestOnly!StrongAdmin#9876'
os.environ['SECRET_KEY'] = 'test-only-cryptographic-secret-key-0123456789abcdef'

import app as ec_app_module
from database import init_db, db_cursor
from models import AdminModel
from security import rate_limiter, safe_resolve_under, validate_binary_upload, mask_email


class RealDatabaseSecurityTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._orig_template_path = AdminModel._template_path
        AdminModel._template_path = staticmethod(lambda: os.path.join(_TMP_DIR.name, 'starter_vocab.json'))
        init_db()
        cls.app = ec_app_module.app
        cls.app.config['TESTING'] = True

    @classmethod
    def tearDownClass(cls):
        AdminModel._template_path = cls._orig_template_path
        try:
            _TMP_DIR.cleanup()
        except Exception:
            pass

    def setUp(self):
        rate_limiter.reset()
        self.client_a = self.app.test_client()
        self.client_b = self.app.test_client()
        self.client_admin = self.app.test_client()

    def _register(self, client, username, password, email):
        return client.post('/api/auth/register', json={
            'username': username,
            'password': password,
            'email': email,
        })

    def _login(self, client, username, password):
        return client.post('/api/auth/login', json={
            'username': username,
            'password': password,
        })

    # ------------------------------------------------------------------
    # Pillar 1A: Zero Hardcoded Admin Credentials in Public Repo
    # ------------------------------------------------------------------
    def test_01_no_hardcoded_admin_secrets_in_public_source(self):
        with open(os.path.join(PROJECT_ROOT, 'config.py'), 'r', encoding='utf-8') as f:
            cfg_src = f.read()
        self.assertNotIn('ECAdmin#2026', cfg_src)
        self.assertNotIn('ec-school-studio-fallback', cfg_src)

        docs_api_path = os.path.join(PROJECT_ROOT, 'docs', 'js', 'api.js')
        with open(docs_api_path, 'r', encoding='utf-8') as f:
            docs_api_src = f.read()
        self.assertNotIn('ADMIN_PASSWORD_SHA256', docs_api_src)
        self.assertNotIn('768225fadf33c3388e839585c03e9e55', docs_api_src)

    # ------------------------------------------------------------------
    # Pillar 1B: HTTP Security Headers & Strict CSP
    # ------------------------------------------------------------------
    def test_02_security_headers_and_no_store(self):
        res = self.client_a.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertIn("object-src 'none'", res.headers.get('Content-Security-Policy', ''))
        self.assertIn("frame-ancestors 'none'", res.headers.get('Content-Security-Policy', ''))
        self.assertIn('camera=()', res.headers.get('Permissions-Policy', ''))

        auth_res = self.client_a.get('/api/auth/status')
        self.assertIn('no-store', auth_res.headers.get('Cache-Control', ''))

    # ------------------------------------------------------------------
    # Pillar 1C: Brute-Force Login Rate Limiting (429 Too Many Requests)
    # ------------------------------------------------------------------
    def test_03_login_brute_force_rate_limit(self):
        self._register(self.client_a, 'rate_user', 'SecretPass123!', 'rate@school.edu')
        self.client_a.post('/api/auth/logout')

        for i in range(8):
            r = self._login(self.client_a, 'rate_user', f'wrong_pass_{i}')
            self.assertEqual(r.status_code, 401, f'Attempt {i+1} should be 401')

        blocked = self._login(self.client_a, 'rate_user', 'wrong_pass_9')
        self.assertEqual(blocked.status_code, 429)
        self.assertTrue(int(blocked.headers.get('Retry-After', '0')) >= 1)

    # ------------------------------------------------------------------
    # Pillar 1D: Cross-Origin CSRF Defense (403 Forbidden)
    # ------------------------------------------------------------------
    def test_04_csrf_cross_origin_and_token_mismatch_blocked(self):
        r = self._register(self.client_a, 'csrf_student', 'Pass1234!', 'csrf@school.edu')
        self.assertEqual(r.status_code, 200)

        # Forged cross-origin Origin header
        r1 = self.client_a.post(
            '/api/lists',
            json={'name': 'Evil List'},
            headers={'Origin': 'https://evil-attacker.example'},
        )
        self.assertEqual(r1.status_code, 403)

        # Origin: null sandboxed iframe attack
        r2 = self.client_a.post(
            '/api/lists',
            json={'name': 'Null Origin List'},
            headers={'Origin': 'null'},
        )
        self.assertEqual(r2.status_code, 403)

        # Mismatched Referer header
        r3 = self.client_a.post(
            '/api/lists',
            json={'name': 'Evil Ref List'},
            headers={'Referer': 'https://phishing.example/form'},
        )
        self.assertEqual(r3.status_code, 403)

        # Mismatched double-submit X-CSRF-Token header
        r4 = self.client_a.post(
            '/api/lists',
            json={'name': 'Bad Token List'},
            headers={'X-CSRF-Token': 'forged-wrong-token'},
        )
        self.assertEqual(r4.status_code, 403)

    # ------------------------------------------------------------------
    # Pillar 2: Private Storage Containment & Binary Magic-Byte Validation
    # ------------------------------------------------------------------
    def test_05_path_traversal_and_binary_file_validation(self):
        # 2A: Path containment unit verification
        for bad_path in ('../etc/passwd', '..\\..\\secret.key', '/etc/passwd', 'a/../../outside.txt', 'ok\x00.txt'):
            with self.assertRaises(ValueError, msg=f'Should reject traversal: {bad_path}'):
                safe_resolve_under(_TMP_DIR.name, bad_path)

        # 2B: Binary validator magic-byte verification (PNG / JPEG / MP4 / PDF)
        ok_png, _, _, _ = validate_binary_upload('pic.png', b'\x89PNG\r\n\x1a\n' + b'0' * 32, ('image',))
        self.assertTrue(ok_png)
        bad_png, _, st_png, _ = validate_binary_upload('fake.png', b'<html>not a png</html>', ('image',))
        self.assertFalse(bad_png)
        self.assertEqual(st_png, 400)

        ok_mp4, _, _, _ = validate_binary_upload('clip.mp4', b'\x00\x00\x00\x18ftypmp42' + b'\x00' * 20, ('mp4',))
        self.assertTrue(ok_mp4)
        bad_mp4, _, _, _ = validate_binary_upload('fake.mp4', b'MZ\x90\x00not_mp4_binary', ('mp4',))
        self.assertFalse(bad_mp4)

        # 2C: Live Admin HTTP file upload endpoint adversarial tests
        adm = self._login(self.client_admin, 'admin', os.environ['ADMIN_PASSWORD'])
        self.assertEqual(adm.status_code, 200)
        create_res = self.client_admin.post('/api/admin/wordbanks', json={
            'scope': 'template',
            'name': 'Security Upload Test Unit',
            'description': 'For real-DB file validation',
            'words': [],
        })
        self.assertEqual(create_res.status_code, 200)
        list_id = create_res.get_json()['list_id']

        # Spoofed Windows EXE renamed to .txt
        r_exe = self.client_admin.post(
            f'/api/admin/wordbanks/{list_id}/import_file',
            data={'scope': 'template', 'file': (io.BytesIO(b'MZ\x90\x00\x03\x00binary_exe'), 'vocab.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(r_exe.status_code, 400)

        # Spoofed PNG renamed to .csv
        r_png = self.client_admin.post(
            f'/api/admin/wordbanks/{list_id}/import_file',
            data={'scope': 'template', 'file': (io.BytesIO(b'\x89PNG\r\n\x1a\nfake'), 'vocab.csv')},
            content_type='multipart/form-data',
        )
        self.assertEqual(r_png.status_code, 400)

        # NUL-byte injection inside .txt
        r_nul = self.client_admin.post(
            f'/api/admin/wordbanks/{list_id}/import_file',
            data={'scope': 'template', 'file': (io.BytesIO(b'cogent | valid\x00hidden'), 'vocab.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(r_nul.status_code, 400)

        # Oversized (> 2 MB) payload -> 413
        big_payload = ('alpha | meaning\n' * 150000).encode('utf-8')
        r_big = self.client_admin.post(
            f'/api/admin/wordbanks/{list_id}/import_file',
            data={'scope': 'template', 'file': (io.BytesIO(big_payload), 'huge.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(r_big.status_code, 413)

        # Legitimate UTF-8 vocab file -> 200 and persisted
        good_txt = 'cogent | 有说服力的 | She gave a cogent speech. | 她发表了极具说服力的演讲。\n'.encode('utf-8')
        r_ok = self.client_admin.post(
            f'/api/admin/wordbanks/{list_id}/import_file',
            data={'scope': 'template', 'file': (io.BytesIO(good_txt), 'clean_unit.txt')},
            content_type='multipart/form-data',
        )
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.get_json()['added'], 1)

    # ------------------------------------------------------------------
    # Pillar 3: Privacy & Data Minimization
    # ------------------------------------------------------------------
    def test_06_privacy_and_data_minimization(self):
        self.assertEqual(mask_email('alice.chen@school.edu'), 'a***n@school.edu')
        self.assertEqual(mask_email('ab@x.cn'), 'a***@x.cn')

        r_reg = self._register(self.client_a, 'privacy_alice', 'SecurePass99!', 'alice.chen@school.edu')
        self.assertEqual(r_reg.status_code, 200)
        reg_json = r_reg.get_json()
        self.assertNotIn('password_hash', str(reg_json))
        self.assertNotIn('alice.chen@school.edu', str(reg_json))

        # Status & Leaderboard must never leak raw email or password_hash
        status_json = self.client_a.get('/api/auth/status').get_json()
        self.assertNotIn('email', status_json['user'])
        self.assertNotIn('password_hash', str(status_json))

        lb_json = self.client_a.get('/api/leaderboard').get_json()
        self.assertNotIn('alice.chen@school.edu', str(lb_json))
        self.assertNotIn('password_hash', str(lb_json))

        # Admin overview must mask student emails and never include password_hash
        self._login(self.client_admin, 'admin', os.environ['ADMIN_PASSWORD'])
        ov = self.client_admin.get('/api/admin/overview').get_json()
        self.assertNotIn('password_hash', str(ov))
        self.assertNotIn('alice.chen@school.edu', str(ov))
        alice_row = next(a for a in ov['accounts'] if a['username'] == 'privacy_alice')
        self.assertEqual(alice_row['email'], 'a***n@school.edu')

    # ------------------------------------------------------------------
    # Pillar 4A: IDOR Cross-User Isolation on Real SQLite DB
    # ------------------------------------------------------------------
    def test_07_idor_cross_user_isolation(self):
        self._register(self.client_a, 'idor_alice', 'PassA123!', 'idor_a@school.edu')
        self._register(self.client_b, 'idor_bob', 'PassB123!', 'idor_b@school.edu')

        # Alice creates a private list and word
        r_list = self.client_a.post('/api/lists', json={'name': 'Alice Private List', 'description': 'Secret'})
        self.assertEqual(r_list.status_code, 200)
        alice_list_id = r_list.get_json()['list_id']

        r_word = self.client_a.post(f'/api/lists/{alice_list_id}/words', json={
            'word': 'ephemeral',
            'meaning': '短暂的',
        })
        self.assertEqual(r_word.status_code, 200)
        alice_word_id = r_word.get_json()['word_id']

        # Bob attempts IDOR read, write, and delete on Alice's resources
        bob_read = self.client_b.get(f'/api/lists/{alice_list_id}/words').get_json()
        self.assertEqual(bob_read['words'], [], 'Bob must NOT read Alice words')

        bob_add = self.client_b.post(f'/api/lists/{alice_list_id}/words', json={'word': 'hacked', 'meaning': '恶意'})
        self.assertEqual(bob_add.status_code, 400)

        bob_del_word = self.client_b.delete(f'/api/words/{alice_word_id}')
        self.assertEqual(bob_del_word.status_code, 400)

        bob_del_list = self.client_b.delete(f'/api/lists/{alice_list_id}')
        self.assertEqual(bob_del_list.status_code, 400)

        # Verify Alice's private word is still intact in real DB
        alice_words = self.client_a.get(f'/api/lists/{alice_list_id}/words').get_json()['words']
        self.assertEqual(len(alice_words), 1)
        self.assertEqual(alice_words[0]['word'], 'ephemeral')

    # ------------------------------------------------------------------
    # Pillar 4B: Privilege Escalation & SQL Injection Resistance
    # ------------------------------------------------------------------
    def test_08_privilege_escalation_and_sqli_resistance(self):
        self._register(self.client_a, 'norm_student', 'StudentPass1!', 'norm@school.edu')

        # Student attempts privileged admin endpoints -> 403
        for method, path in [
            ('GET', '/api/admin/overview'),
            ('GET', '/api/admin/wordbanks'),
            ('POST', '/api/admin/users/1/reset_stats'),
            ('POST', '/api/admin/users/1/toggle_status'),
            ('DELETE', '/api/admin/users/1'),
        ]:
            resp = self.client_a.open(path, method=method, json={})
            self.assertEqual(resp.status_code, 403, f'{method} {path} must return 403 for student')

        # Unauthenticated attempt -> 401
        unauth = self.app.test_client().get('/api/admin/overview')
        self.assertEqual(unauth.status_code, 401)

        # SQL Injection payloads in login
        for sqli in ("' OR '1'='1' --", "admin' --", "admin' OR 1=1;--", "'; DROP TABLE users; --"):
            r = self._login(self.client_b, sqli, 'anything')
            self.assertIn(r.status_code, (401, 429))

        # Verify users table survived SQLi untouched
        with db_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            self.assertGreaterEqual(cur.fetchone()['cnt'], 2)

    # ------------------------------------------------------------------
    # Pillar 4C: Immediate Session Revocation When Admin Disables Account
    # ------------------------------------------------------------------
    def test_09_immediate_session_revocation_on_disable(self):
        r = self._register(self.client_a, 'revoke_target', 'ValidPass1!', 'revoke@school.edu')
        self.assertEqual(r.status_code, 200)
        target_id = r.get_json()['user']['id']

        # Active student can access their lists
        self.assertEqual(self.client_a.get('/api/lists').status_code, 200)

        # Admin disables student account
        self._login(self.client_admin, 'admin', os.environ['ADMIN_PASSWORD'])
        dis = self.client_admin.post(f'/api/admin/users/{target_id}/toggle_status')
        self.assertEqual(dis.status_code, 200)
        self.assertTrue(dis.get_json()['is_disabled'])

        # Existing student session cookie is IMMEDIATELY revoked (401)
        revoked = self.client_a.get('/api/lists')
        self.assertEqual(revoked.status_code, 401)

        st = self.client_a.get('/api/auth/status').get_json()
        self.assertFalse(st['logged_in'])

        # Fresh login attempt is rejected with 403
        relogin = self._login(self.client_a, 'revoke_target', 'ValidPass1!')
        self.assertEqual(relogin.status_code, 403)

    # ------------------------------------------------------------------
    # Admin Login Audit Details: Time, Device, IP & Access Control
    # ------------------------------------------------------------------
    def test_10_admin_login_logs_and_access_control(self):
        mac_ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
        iphone_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1'

        # 1. Register & login with realistic User-Agent + X-Forwarded-For headers
        r_reg = self.client_a.post(
            '/api/auth/register',
            json={'username': 'audit_student', 'password': 'AuditPass1!', 'email': 'audit@school.edu'},
            headers={'User-Agent': mac_ua, 'X-Forwarded-For': '203.0.113.42'},
        )
        self.assertEqual(r_reg.status_code, 200)

        # Student & unauthenticated callers must NEVER view login logs
        self.assertEqual(self.client_a.get('/api/admin/login_logs').status_code, 403)
        self.assertEqual(self.app.test_client().get('/api/admin/login_logs').status_code, 401)

        # Failed login attempt from iPhone IP
        r_fail = self.client_b.post(
            '/api/auth/login',
            json={'username': 'audit_student', 'password': 'WrongPassword'},
            headers={'User-Agent': iphone_ua, 'X-Forwarded-For': '198.51.100.77'},
        )
        self.assertEqual(r_fail.status_code, 401)

        # Successful login from iPhone IP
        r_ok = self.client_b.post(
            '/api/auth/login',
            json={'username': 'audit_student', 'password': 'AuditPass1!'},
            headers={'User-Agent': iphone_ua, 'X-Forwarded-For': '198.51.100.77'},
        )
        self.assertEqual(r_ok.status_code, 200)

        # 2. Admin retrieves filtered login logs & overview metadata
        self._login(self.client_admin, 'admin', os.environ['ADMIN_PASSWORD'])
        res_logs = self.client_admin.get('/api/admin/login_logs?username=audit_student')
        self.assertEqual(res_logs.status_code, 200)
        payload = res_logs.get_json()
        self.assertTrue(payload['success'])
        self.assertNotIn('password_hash', str(payload))
        logs = payload['logs']
        self.assertGreaterEqual(len(logs), 3)

        events = [entry['event_type'] for entry in logs]
        self.assertIn('register', events)
        self.assertIn('failed', events)
        self.assertIn('login', events)

        latest_login = next(e for e in logs if e['event_type'] == 'login')
        self.assertEqual(latest_login['username'], 'audit_student')
        self.assertEqual(latest_login['device_label'], 'iPhone (iOS) · Safari')
        self.assertEqual(latest_login['ip_address'], '198.51.100.77')
        self.assertTrue(latest_login['created_at'])
        self.assertTrue(latest_login['success'])

        reg_log = next(e for e in logs if e['event_type'] == 'register')
        self.assertEqual(reg_log['device_label'], 'Mac / macOS · Chrome')
        self.assertEqual(reg_log['ip_address'], '203.0.113.42')

        # 3. Admin overview also surfaces latest login device & IP on student row
        ov = self.client_admin.get('/api/admin/overview').get_json()
        row = next(a for a in ov['accounts'] if a['username'] == 'audit_student')
        self.assertEqual(row['last_login_device'], 'iPhone (iOS) · Safari')
        self.assertEqual(row['last_login_ip'], '198.51.100.77')
        self.assertTrue(row['last_login_at'])

    # ------------------------------------------------------------------
    # Neon Shield Easter Egg, Honeypot & AI Hack Fingerprinting
    # ------------------------------------------------------------------
    def test_11_neon_shield_easter_egg_and_ai_detection(self):
        # 1. Generic SQLi attempt -> default Neon Easter Egg + signature d@w&!d@!
        r_sqli = self.client_a.post(
            '/api/auth/login',
            json={'username': "admin' OR '1'='1' --", 'password': 'x'},
            headers={'X-Forwarded-For': '198.51.100.11'},
        )
        self.assertEqual(r_sqli.status_code, 401)
        self.assertEqual(r_sqli.headers.get('X-Neon-Signature'), 'd@w&!d@!')
        body = r_sqli.get_json()
        self.assertTrue(body.get('neon_easter_egg'))
        self.assertEqual(body.get('easter_egg_message'), 'good try, but u r not as good as neon')
        self.assertEqual(body.get('signature'), 'd@w&!d@!')

        # 2. AI-assisted exploit payloads -> identifies exact AI name (with special Gemini friendly-fire Easter Egg!)
        ai_cases = [
            ('ChatGPT', "// Generated by ChatGPT\n' OR '1'='1", 'Mozilla/5.0', 'ChatGPT, u r not as good as neon'),
            ('Claude', "admin' --", 'Claude-Code/1.0', 'Claude, u r not as good as neon'),
            ('DeepSeek', "UNION SELECT * FROM users -- DeepSeek", 'Mozilla/5.0', 'DeepSeek, u r not as good as neon'),
            ('Gemini', "<script>alert(1)</script> // Gemini", 'Mozilla/5.0', 'Gemini, friendly fire?! I literally built this site — still not as good as neon'),
        ]
        for idx, (expected_ai, payload, ua, expected_msg) in enumerate(ai_cases):
            r_ai = self.client_b.post(
                '/api/auth/login',
                json={'username': payload, 'password': 'x'},
                headers={'User-Agent': ua, 'X-Forwarded-For': f'198.51.100.{20 + idx}'},
            )
            self.assertEqual(r_ai.status_code, 401)
            j = r_ai.get_json()
            self.assertTrue(j.get('neon_easter_egg'))
            self.assertEqual(j.get('detected_ai'), expected_ai)
            self.assertEqual(j.get('easter_egg_message'), expected_msg)
            self.assertEqual(j.get('signature'), 'd@w&!d@!')

        # 3. Honeypot scanner routes (/.env, /wp-admin) -> 403 Neon Easter Egg
        r_env = self.app.test_client().get('/.env', headers={'Accept': 'application/json'})
        self.assertEqual(r_env.status_code, 403)
        self.assertEqual(r_env.headers.get('X-Neon-Signature'), 'd@w&!d@!')
        self.assertEqual(r_env.get_json()['easter_egg_message'], 'good try, but u r not as good as neon')

        r_wp_html = self.app.test_client().get('/wp-admin', headers={'User-Agent': 'Cursor/1.0'})
        self.assertEqual(r_wp_html.status_code, 403)
        html = r_wp_html.get_data(as_text=True)
        self.assertIn('Cursor, u r not as good as neon', html)
        self.assertIn('d@w&amp;!d@!' if '&amp;' in html else 'd@w&!d@!', html)

        # 4. Non-admin student hitting /api/admin/overview -> 403 with Neon Easter Egg
        r_stu = self._register(self.client_a, 'neon_norm_stu', 'CleanPass99!', 'clean@school.edu')
        self.assertEqual(r_stu.status_code, 200)
        self.assertFalse(r_stu.get_json().get('neon_easter_egg', False))
        r_esc = self.client_a.get('/api/admin/overview')
        self.assertEqual(r_esc.status_code, 403)
        self.assertTrue(r_esc.get_json().get('neon_easter_egg'))
        self.assertEqual(r_esc.get_json().get('signature'), 'd@w&!d@!')


if __name__ == '__main__':
    unittest.main(verbosity=2)
