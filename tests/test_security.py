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


if __name__ == '__main__':
    unittest.main(verbosity=2)
