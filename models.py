import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from config import BASE_DIR, DATA_DIR
from database import db_cursor
from security import mask_email


def _load_starter_seed():
    candidates = [
        os.path.join(BASE_DIR, 'data', 'starter_vocab.json'),
        os.path.join(BASE_DIR, 'docs', 'data', 'vocab.json'),
    ]
    for seed_path in candidates:
        if os.path.exists(seed_path):
            try:
                with open(seed_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data.get('lists'), list) and isinstance(data.get('words'), list):
                    return data
            except Exception:
                pass
    return None


class UserModel:
    @staticmethod
    def get_by_id(user_id):
        with db_cursor(commit=False) as cur:
            cur.execute("SELECT id, email, username, COALESCE(is_admin, 0) AS is_admin, COALESCE(is_disabled, 0) AS is_disabled, created_at FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            if not row or row['is_disabled']:
                return None
            d = dict(row)
            d['is_admin'] = bool(d['is_admin'])
            d['is_disabled'] = bool(d['is_disabled'])
            return d

    @staticmethod
    def register(username, password, email=''):
        username = (username or '').strip()
        password = password or ''
        email = (email or '').strip()

        if len(username) < 2:
            raise ValueError("用户名至少需要 2 个字符")
        if len(password) < 4:
            raise ValueError("密码至少需要 4 个字符")

        if not email:
            email = f"{username.lower()}@ec.local"

        pw_hash = generate_password_hash(password)

        with db_cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)",
                (username, email)
            )
            if cur.fetchone():
                raise ValueError("该用户名或邮箱已被注册")

            cur.execute(
                "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
                (email, username, pw_hash)
            )
            new_user_id = cur.lastrowid
            cur.execute(
                "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
                (new_user_id,)
            )

            # Seed starter EC lists/words for the newly registered user
            seed = _load_starter_seed()
            if seed:
                old_to_new_list = {}
                for lst in seed['lists']:
                    cur.execute(
                        "INSERT INTO vocab_lists (user_id, name, description, sort_order) VALUES (?, ?, ?, ?)",
                        (new_user_id, lst['name'], lst.get('description', ''), lst.get('sort_order', 0))
                    )
                    old_to_new_list[lst['id']] = cur.lastrowid

                for w in seed['words']:
                    target_lid = old_to_new_list.get(w['list_id'])
                    if target_lid:
                        cur.execute(
                            """INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                target_lid,
                                new_user_id,
                                w['word'],
                                w['meaning'],
                                w.get('phonetic', ''),
                                w.get('example_en', ''),
                                w.get('example_cn', '')
                            )
                        )

            return {'id': new_user_id, 'username': username, 'email': email, 'is_admin': False}

    @staticmethod
    def authenticate(identifier, password):
        identifier = (identifier or '').strip()
        password = password or ''
        if not identifier or not password:
            return None

        with db_cursor(commit=False) as cur:
            cur.execute(
                """SELECT id, email, username, password_hash,
                          COALESCE(is_admin, 0) AS is_admin,
                          COALESCE(is_disabled, 0) AS is_disabled
                   FROM users
                   WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)""",
                (identifier, identifier)
            )
            row = cur.fetchone()
            if not row:
                return None

            stored_hash = row['password_hash'] or ''
            if not stored_hash:
                return None

            if not check_password_hash(stored_hash, password):
                return None

            if row['is_disabled']:
                raise PermissionError("该账号已被管理员停用，请联系老师恢复")

            return {
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'is_admin': bool(row['is_admin'])
            }


class VocabListModel:
    @staticmethod
    def get_all_lists(user_id):
        """Retrieve all vocabulary lists for a user sorted by defined order"""
        with db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT vl.id, vl.name, vl.description, vl.sort_order, vl.created_at,
                       COUNT(w.id) as word_count
                FROM vocab_lists vl
                LEFT JOIN words w ON vl.id = w.list_id
                WHERE vl.user_id = ?
                GROUP BY vl.id
                ORDER BY vl.sort_order ASC, vl.id ASC
            """, (user_id,))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def create(user_id, name, description=''):
        name = name.strip()
        if not name:
            raise ValueError("词库名称不能为空")
        with db_cursor() as cur:
            cur.execute("SELECT MAX(sort_order) FROM vocab_lists WHERE user_id = ?", (user_id,))
            max_order = cur.fetchone()[0] or 0
            cur.execute("""
                INSERT INTO vocab_lists (user_id, name, description, sort_order)
                VALUES (?, ?, ?, ?)
            """, (user_id, name, description.strip(), max_order + 1))
            return cur.lastrowid

    @staticmethod
    def delete(user_id, list_id):
        with db_cursor() as cur:
            cur.execute("DELETE FROM words WHERE list_id = ? AND user_id = ?", (list_id, user_id))
            cur.execute("DELETE FROM vocab_lists WHERE id = ? AND user_id = ?", (list_id, user_id))
            return cur.rowcount > 0


class WordModel:
    @staticmethod
    def _verify_list_owner(cur, user_id, list_id):
        cur.execute("SELECT 1 FROM vocab_lists WHERE id = ? AND user_id = ?", (list_id, user_id))
        if not cur.fetchone():
            raise ValueError("词库不存在或无权限")

    @staticmethod
    def get_words_by_list(user_id, list_id):
        with db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT id, list_id, word, meaning, phonetic, example_en, example_cn,
                       wrong_count, correct_count, mastered, created_at
                FROM words
                WHERE list_id = ? AND user_id = ?
                ORDER BY id ASC
            """, (list_id, user_id))
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def add_word(user_id, list_id, word, meaning, phonetic='', example_en='', example_cn=''):
        word = word.strip()
        meaning = meaning.strip()
        if not word or not meaning:
            raise ValueError("英文单词和中文释义均不能为空")
        with db_cursor() as cur:
            WordModel._verify_list_owner(cur, user_id, list_id)
            cur.execute("""
                INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (list_id, user_id, word, meaning, phonetic.strip(), example_en.strip(), example_cn.strip()))
            return cur.lastrowid

    @staticmethod
    def batch_add_words(user_id, list_id, word_items):
        added = 0
        with db_cursor() as cur:
            WordModel._verify_list_owner(cur, user_id, list_id)
            for item in word_items:
                w = item.get('word', '').strip()
                m = item.get('meaning', '').strip()
                if not w or not m:
                    continue
                p = item.get('phonetic', '').strip()
                een = item.get('example_en', '').strip()
                ecn = item.get('example_cn', '').strip()
                cur.execute("""
                    INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (list_id, user_id, w, m, p, een, ecn))
                added += 1
        return added

    @staticmethod
    def delete_word(user_id, word_id):
        with db_cursor() as cur:
            cur.execute("DELETE FROM words WHERE id = ? AND user_id = ?", (word_id, user_id))
            return cur.rowcount > 0

    @staticmethod
    def get_words_by_ids(user_id, word_ids):
        clean_ids = [int(wid) for wid in word_ids if wid is not None]
        if not clean_ids:
            return {}
        placeholders = ','.join(['?'] * len(clean_ids))
        with db_cursor(commit=False) as cur:
            cur.execute(f"""
                SELECT id, list_id, word, meaning, phonetic, example_en, example_cn
                FROM words
                WHERE user_id = ? AND id IN ({placeholders})
            """, [user_id] + clean_ids)
            return {r['id']: dict(r) for r in cur.fetchall()}

    @staticmethod
    def get_extra_random_words(user_id, exclude_words, count=2):
        lowered = [w.strip().lower() for w in exclude_words if w and w.strip()]
        with db_cursor(commit=False) as cur:
            if lowered:
                placeholders = ','.join(['?'] * len(lowered))
                where_clause = f"WHERE user_id = ? AND LOWER(word) NOT IN ({placeholders})"
                params = [user_id] + lowered + [count]
            else:
                where_clause = "WHERE user_id = ?"
                params = [user_id, count]
            sql = f"""
                SELECT MIN(id) AS id, word, meaning, example_en, example_cn
                FROM words
                {where_clause}
                GROUP BY LOWER(word)
                ORDER BY RANDOM()
                LIMIT ?
            """
            cur.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            return rows

    @staticmethod
    def record_answer_stat(user_id, word_id, is_correct):
        if not word_id:
            return
        with db_cursor() as cur:
            if is_correct:
                cur.execute("""
                    UPDATE words
                    SET correct_count = correct_count + 1,
                        mastered = CASE WHEN correct_count + 1 >= 2 THEN 1 ELSE mastered END
                    WHERE id = ? AND user_id = ?
                """, (word_id, user_id))
            else:
                cur.execute("""
                    UPDATE words
                    SET wrong_count = wrong_count + 1,
                        mastered = 0
                    WHERE id = ? AND user_id = ?
                """, (word_id, user_id))


class StatsModel:
    @staticmethod
    def record_vocab_attempt(user_id, is_correct):
        if not user_id:
            return
        with db_cursor() as cur:
            cur.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))
            cur.execute("""
                UPDATE user_stats
                SET vocab_reviewed = vocab_reviewed + 1,
                    vocab_correct = vocab_correct + ?,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (1 if is_correct else 0, user_id))

    @staticmethod
    def record_grammar_attempt(user_id, question_id, topic_id='', is_correct=False):
        if not user_id:
            return
        q_id = (question_id or '').strip()
        t_id = (topic_id or '').strip()
        ok_int = 1 if is_correct else 0
        with db_cursor() as cur:
            cur.execute("INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)", (user_id,))
            cur.execute("""
                UPDATE user_stats
                SET grammar_completed = grammar_completed + 1,
                    grammar_correct = grammar_correct + ?,
                    last_active_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (ok_int, user_id))
            if q_id:
                cur.execute("""
                    INSERT INTO grammar_attempts (user_id, question_id, topic_id, is_correct)
                    VALUES (?, ?, ?, ?)
                """, (user_id, q_id, t_id, ok_int))

    @staticmethod
    def _build_ranked_rows(sort_by='total'):
        with db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT
                    u.id AS user_id,
                    u.username,
                    u.created_at,
                    COALESCE(s.vocab_reviewed, 0) AS vocab_reviewed,
                    COALESCE(s.vocab_correct, 0) AS vocab_correct,
                    COALESCE(s.grammar_completed, 0) AS grammar_completed,
                    COALESCE(s.grammar_correct, 0) AS grammar_correct,
                    COALESCE(s.last_active_at, u.created_at) AS last_active_at,
                    COALESCE((
                        SELECT COUNT(DISTINCT LOWER(w.word))
                        FROM words w
                        WHERE w.user_id = u.id AND w.mastered = 1
                    ), 0) AS vocab_mastered,
                    COALESCE((
                        SELECT COUNT(DISTINCT ga.question_id)
                        FROM grammar_attempts ga
                        WHERE ga.user_id = u.id
                    ), 0) AS grammar_unique
                FROM users u
                LEFT JOIN user_stats s ON s.user_id = u.id
                WHERE u.password_hash IS NOT NULL AND u.password_hash != ''
                  AND COALESCE(u.is_admin, 0) = 0
                  AND COALESCE(u.is_disabled, 0) = 0
            """)
            rows = [dict(r) for r in cur.fetchall()]

        entries = []
        for r in rows:
            vr = int(r['vocab_reviewed'] or 0)
            vc = int(r['vocab_correct'] or 0)
            gc = int(r['grammar_completed'] or 0)
            gok = int(r['grammar_correct'] or 0)
            total_attempts = vr + gc
            total_correct = vc + gok
            acc = round((total_correct / total_attempts) * 100) if total_attempts > 0 else 0
            # Balanced school effort + mastery score
            score = vr * 2 + vc + gc * 3 + gok * 2 + int(r['vocab_mastered'] or 0) * 4
            entries.append({
                'user_id': r['user_id'],
                'username': r['username'],
                'vocab_reviewed': vr,
                'vocab_correct': vc,
                'vocab_mastered': int(r['vocab_mastered'] or 0),
                'grammar_completed': gc,
                'grammar_correct': gok,
                'grammar_unique': int(r['grammar_unique'] or 0),
                'accuracy_pct': acc,
                'total_score': score,
                'last_active_at': r['last_active_at'] or '',
            })

        if sort_by == 'vocab':
            entries.sort(key=lambda x: (-x['vocab_reviewed'], -x['vocab_mastered'], -x['total_score'], x['username'].lower()))
        elif sort_by == 'grammar':
            entries.sort(key=lambda x: (-x['grammar_completed'], -x['grammar_unique'], -x['total_score'], x['username'].lower()))
        else:
            entries.sort(key=lambda x: (-x['total_score'], -(x['vocab_reviewed'] + x['grammar_completed']), x['username'].lower()))

        for idx, item in enumerate(entries, start=1):
            item['rank'] = idx
        return entries

    @staticmethod
    def get_leaderboard(sort_by='total', current_user_id=None, limit=100):
        sort_key = sort_by if sort_by in ('total', 'vocab', 'grammar') else 'total'
        entries = StatsModel._build_ranked_rows(sort_key)
        my_entry = None
        for item in entries:
            item['is_me'] = (current_user_id is not None and item['user_id'] == current_user_id)
            if item['is_me']:
                my_entry = item
        return {
            'sort': sort_key,
            'total_students': len(entries),
            'my_rank': my_entry,
            'entries': entries[:limit],
        }

    @staticmethod
    def get_user_summary(user_id):
        lb = StatsModel.get_leaderboard(sort_by='total', current_user_id=user_id, limit=500)
        if lb['my_rank']:
            summary = dict(lb['my_rank'])
            summary['total_students'] = lb['total_students']
            return summary
        return {
            'user_id': user_id,
            'username': '',
            'rank': None,
            'total_students': lb['total_students'],
            'vocab_reviewed': 0,
            'vocab_correct': 0,
            'vocab_mastered': 0,
            'grammar_completed': 0,
            'grammar_correct': 0,
            'grammar_unique': 0,
            'accuracy_pct': 0,
            'total_score': 0,
            'last_active_at': '',
        }


class AdminModel:
    @staticmethod
    def _template_path():
        return os.path.join(DATA_DIR, 'starter_vocab.json')

    @staticmethod
    def load_template():
        t_path = AdminModel._template_path()
        data = None
        if os.path.exists(t_path):
            try:
                with open(t_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded.get('lists'), list) and isinstance(loaded.get('words'), list):
                    data = loaded
            except Exception:
                data = None
        if not data:
            data = _load_starter_seed()
        if not data:
            return {'lists': [], 'words': []}
        return {
            'lists': [dict(l) for l in data.get('lists', [])],
            'words': [dict(w) for w in data.get('words', [])],
        }

    @staticmethod
    def save_template(data):
        t_path = AdminModel._template_path()
        os.makedirs(os.path.dirname(t_path), exist_ok=True)
        with open(t_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def get_overview():
        with db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT
                    u.id,
                    u.username,
                    u.email,
                    COALESCE(u.is_admin, 0) AS is_admin,
                    COALESCE(u.is_disabled, 0) AS is_disabled,
                    u.created_at,
                    COALESCE(s.vocab_reviewed, 0) AS vocab_reviewed,
                    COALESCE(s.vocab_correct, 0) AS vocab_correct,
                    COALESCE(s.grammar_completed, 0) AS grammar_completed,
                    COALESCE(s.grammar_correct, 0) AS grammar_correct,
                    COALESCE(s.last_active_at, u.created_at) AS last_active_at,
                    COALESCE((SELECT COUNT(*) FROM vocab_lists vl WHERE vl.user_id = u.id), 0) AS list_count,
                    COALESCE((SELECT COUNT(*) FROM words w WHERE w.user_id = u.id), 0) AS word_count,
                    COALESCE((SELECT COUNT(DISTINCT LOWER(w.word)) FROM words w WHERE w.user_id = u.id AND w.mastered = 1), 0) AS vocab_mastered,
                    (SELECT ll.ip_address FROM login_logs ll WHERE LOWER(ll.username) = LOWER(u.username) AND ll.success = 1 ORDER BY ll.id DESC LIMIT 1) AS last_login_ip,
                    (SELECT ll.device_label FROM login_logs ll WHERE LOWER(ll.username) = LOWER(u.username) AND ll.success = 1 ORDER BY ll.id DESC LIMIT 1) AS last_login_device,
                    (SELECT ll.created_at FROM login_logs ll WHERE LOWER(ll.username) = LOWER(u.username) AND ll.success = 1 ORDER BY ll.id DESC LIMIT 1) AS last_login_at
                FROM users u
                LEFT JOIN user_stats s ON s.user_id = u.id
                WHERE u.password_hash IS NOT NULL AND u.password_hash != ''
                ORDER BY COALESCE(u.is_admin, 0) DESC, u.created_at DESC
            """)
            rows = [dict(r) for r in cur.fetchall()]

        accounts = []
        total_vocab = 0
        total_grammar = 0
        student_count = 0
        for r in rows:
            vr = int(r['vocab_reviewed'] or 0)
            vc = int(r['vocab_correct'] or 0)
            gc = int(r['grammar_completed'] or 0)
            gok = int(r['grammar_correct'] or 0)
            tot = vr + gc
            acc = round(((vc + gok) / tot) * 100) if tot > 0 else 0
            score = vr * 2 + vc + gc * 3 + gok * 2 + int(r['vocab_mastered'] or 0) * 4
            is_adm = bool(r['is_admin'])
            if not is_adm:
                student_count += 1
                total_vocab += vr
                total_grammar += gc
            accounts.append({
                'id': r['id'],
                'username': r['username'],
                'email': mask_email(r['email']),
                'is_admin': is_adm,
                'is_disabled': bool(r['is_disabled']),
                'created_at': r['created_at'] or '',
                'last_active_at': r['last_active_at'] or '',
                'vocab_reviewed': vr,
                'vocab_correct': vc,
                'vocab_mastered': int(r['vocab_mastered'] or 0),
                'grammar_completed': gc,
                'grammar_correct': gok,
                'accuracy_pct': acc,
                'total_score': score,
                'list_count': int(r['list_count'] or 0),
                'word_count': int(r['word_count'] or 0),
                'last_login_ip': r['last_login_ip'] or '',
                'last_login_device': r['last_login_device'] or '',
                'last_login_at': r['last_login_at'] or '',
            })

        tpl = AdminModel.load_template()
        return {
            'summary': {
                'student_count': student_count,
                'total_vocab_reviewed': total_vocab,
                'total_grammar_completed': total_grammar,
                'template_list_count': len(tpl['lists']),
                'template_word_count': len(tpl['words']),
            },
            'accounts': accounts,
        }

    @staticmethod
    def record_login_log(user_id, username, event_type='login', ip_address='', device_label='', user_agent='', success=True):
        uname = (username or '').strip()[:80]
        if not uname:
            return
        with db_cursor() as cur:
            cur.execute(
                """
                INSERT INTO login_logs (user_id, username, event_type, ip_address, device_label, user_agent, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    uname,
                    (event_type or 'login')[:24],
                    (ip_address or '')[:64],
                    (device_label or '')[:80],
                    (user_agent or '')[:180],
                    1 if success else 0,
                )
            )

    @staticmethod
    def get_login_logs(username_filter='', limit=150):
        lim = max(1, min(int(limit or 150), 500))
        uf = (username_filter or '').strip()
        with db_cursor(commit=False) as cur:
            if uf:
                cur.execute(
                    """
                    SELECT id, user_id, username, event_type, ip_address, device_label, user_agent, success, created_at
                    FROM login_logs
                    WHERE LOWER(username) = LOWER(?)
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (uf, lim)
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, username, event_type, ip_address, device_label, user_agent, success, created_at
                    FROM login_logs
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (lim,)
                )
            return [
                {
                    'id': r['id'],
                    'user_id': r['user_id'],
                    'username': r['username'],
                    'event_type': r['event_type'] or 'login',
                    'ip_address': r['ip_address'] or 'unknown',
                    'device_label': r['device_label'] or 'Unknown Device',
                    'user_agent': r['user_agent'] or '',
                    'success': bool(r['success']),
                    'created_at': r['created_at'] or '',
                }
                for r in cur.fetchall()
            ]

    @staticmethod
    def reset_password(target_user_id, new_password):
        new_password = (new_password or '').strip()
        if len(new_password) < 4:
            raise ValueError("新密码至少需要 4 个字符")
        pw_hash = generate_password_hash(new_password)
        with db_cursor() as cur:
            cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, target_user_id))
            if cur.rowcount == 0:
                raise ValueError("目标账号不存在")

    @staticmethod
    def toggle_disabled(target_user_id):
        with db_cursor() as cur:
            cur.execute("SELECT id, COALESCE(is_admin, 0) AS is_admin, COALESCE(is_disabled, 0) AS is_disabled FROM users WHERE id = ?", (target_user_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("目标账号不存在")
            if row['is_admin']:
                raise ValueError("不能停用管理员账号")
            new_val = 0 if row['is_disabled'] else 1
            cur.execute("UPDATE users SET is_disabled = ? WHERE id = ?", (new_val, target_user_id))
            return bool(new_val)

    @staticmethod
    def reset_user_stats(target_user_id):
        with db_cursor() as cur:
            cur.execute("UPDATE user_stats SET vocab_reviewed = 0, vocab_correct = 0, grammar_completed = 0, grammar_correct = 0 WHERE user_id = ?", (target_user_id,))
            cur.execute("DELETE FROM grammar_attempts WHERE user_id = ?", (target_user_id,))
            cur.execute("UPDATE words SET correct_count = 0, wrong_count = 0, mastered = 0 WHERE user_id = ?", (target_user_id,))

    @staticmethod
    def delete_user(target_user_id):
        with db_cursor() as cur:
            cur.execute("SELECT id, COALESCE(is_admin, 0) AS is_admin FROM users WHERE id = ?", (target_user_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError("目标账号不存在")
            if row['is_admin']:
                raise ValueError("不能删除管理员账号")
            cur.execute("DELETE FROM users WHERE id = ?", (target_user_id,))

    @staticmethod
    def get_wordbanks(scope='template'):
        if scope == 'template':
            tpl = AdminModel.load_template()
            counts = {}
            for w in tpl['words']:
                lid = w.get('list_id')
                counts[lid] = counts.get(lid, 0) + 1
            lists = []
            for lst in sorted(tpl['lists'], key=lambda x: (x.get('sort_order', 0), x.get('id', 0))):
                lists.append({
                    'id': lst['id'],
                    'name': lst['name'],
                    'description': lst.get('description', ''),
                    'word_count': counts.get(lst['id'], 0),
                })
            return lists
        if scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            return VocabListModel.get_all_lists(uid)
        raise ValueError("无效的词库管理范围")

    @staticmethod
    def get_words_in_bank(scope, list_id):
        list_id = int(list_id)
        if scope == 'template':
            tpl = AdminModel.load_template()
            return [dict(w) for w in tpl['words'] if int(w.get('list_id', -1)) == list_id]
        if scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            return WordModel.get_words_by_list(uid, list_id)
        raise ValueError("无效的词库管理范围")

    @staticmethod
    def broadcast_list_to_all_students(name, description, word_items):
        """Create or merge a word bank into every active student account."""
        name = (name or '').strip()
        description = (description or '').strip()
        if not name:
            return 0
        synced_users = 0
        with db_cursor() as cur:
            cur.execute("""
                SELECT id FROM users
                WHERE password_hash IS NOT NULL AND password_hash != ''
                  AND COALESCE(is_admin, 0) = 0
            """)
            student_ids = [r['id'] for r in cur.fetchall()]
            for uid in student_ids:
                cur.execute(
                    "SELECT id FROM vocab_lists WHERE user_id = ? AND LOWER(name) = LOWER(?)",
                    (uid, name)
                )
                existing = cur.fetchone()
                if existing:
                    target_lid = existing['id']
                    if description:
                        cur.execute("UPDATE vocab_lists SET description = ? WHERE id = ?", (description, target_lid))
                else:
                    cur.execute("SELECT MAX(sort_order) FROM vocab_lists WHERE user_id = ?", (uid,))
                    max_o = cur.fetchone()[0] or 0
                    cur.execute(
                        "INSERT INTO vocab_lists (user_id, name, description, sort_order) VALUES (?, ?, ?, ?)",
                        (uid, name, description, max_o + 1)
                    )
                    target_lid = cur.lastrowid

                cur.execute("SELECT LOWER(word) FROM words WHERE list_id = ? AND user_id = ?", (target_lid, uid))
                existing_words = {r[0] for r in cur.fetchall()}
                for item in (word_items or []):
                    w = (item.get('word') or '').strip()
                    m = (item.get('meaning') or '').strip()
                    if not w or not m or w.lower() in existing_words:
                        continue
                    existing_words.add(w.lower())
                    cur.execute(
                        """INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            target_lid, uid, w, m,
                            (item.get('phonetic') or '').strip(),
                            (item.get('example_en') or '').strip(),
                            (item.get('example_cn') or '').strip(),
                        )
                    )
                synced_users += 1
        return synced_users

    @staticmethod
    def create_wordbank(scope, name, description='', word_items=None, push_to_all=False):
        name = (name or '').strip()
        description = (description or '').strip()
        word_items = word_items or []
        if not name:
            raise ValueError("词库单元名称不能为空")

        created_id = None
        if scope == 'template':
            tpl = AdminModel.load_template()
            next_lid = max([int(l.get('id', 0)) for l in tpl['lists']], default=0) + 1
            next_ord = max([int(l.get('sort_order', 0)) for l in tpl['lists']], default=0) + 1
            next_wid = max([int(w.get('id', 0)) for w in tpl['words']], default=0) + 1
            tpl['lists'].append({
                'id': next_lid,
                'name': name,
                'description': description,
                'sort_order': next_ord,
            })
            for item in word_items:
                w = (item.get('word') or '').strip()
                m = (item.get('meaning') or '').strip()
                if not w or not m:
                    continue
                tpl['words'].append({
                    'id': next_wid,
                    'list_id': next_lid,
                    'word': w,
                    'meaning': m,
                    'phonetic': (item.get('phonetic') or '').strip(),
                    'example_en': (item.get('example_en') or '').strip(),
                    'example_cn': (item.get('example_cn') or '').strip(),
                })
                next_wid += 1
            AdminModel.save_template(tpl)
            created_id = next_lid
        elif scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            created_id = VocabListModel.create(uid, name, description)
            if word_items:
                WordModel.batch_add_words(uid, created_id, word_items)
        else:
            raise ValueError("无效的词库管理范围")

        synced = 0
        if push_to_all:
            synced = AdminModel.broadcast_list_to_all_students(name, description, word_items)

        return {'list_id': created_id, 'pushed_students': synced}

    @staticmethod
    def delete_wordbank(scope, list_id):
        list_id = int(list_id)
        if scope == 'template':
            tpl = AdminModel.load_template()
            tpl['lists'] = [l for l in tpl['lists'] if int(l.get('id', -1)) != list_id]
            tpl['words'] = [w for w in tpl['words'] if int(w.get('list_id', -1)) != list_id]
            AdminModel.save_template(tpl)
            return True
        if scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            return VocabListModel.delete(uid, list_id)
        raise ValueError("无效的词库管理范围")

    @staticmethod
    def add_words_to_bank(scope, list_id, word_items, sync_all=False):
        list_id = int(list_id)
        added = 0
        list_name = ''
        list_desc = ''
        if scope == 'template':
            tpl = AdminModel.load_template()
            target = next((l for l in tpl['lists'] if int(l.get('id', -1)) == list_id), None)
            if not target:
                raise ValueError("模板词库单元不存在")
            list_name = target['name']
            list_desc = target.get('description', '')
            next_wid = max([int(w.get('id', 0)) for w in tpl['words']], default=0) + 1
            for item in word_items:
                w = (item.get('word') or '').strip()
                m = (item.get('meaning') or '').strip()
                if not w or not m:
                    continue
                tpl['words'].append({
                    'id': next_wid,
                    'list_id': list_id,
                    'word': w,
                    'meaning': m,
                    'phonetic': (item.get('phonetic') or '').strip(),
                    'example_en': (item.get('example_en') or '').strip(),
                    'example_cn': (item.get('example_cn') or '').strip(),
                })
                next_wid += 1
                added += 1
            AdminModel.save_template(tpl)
        elif scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            added = WordModel.batch_add_words(uid, list_id, word_items)
        else:
            raise ValueError("无效的词库管理范围")

        synced = 0
        if sync_all and list_name:
            synced = AdminModel.broadcast_list_to_all_students(list_name, list_desc, word_items)
        return {'added': added, 'pushed_students': synced}

    @staticmethod
    def delete_word_from_bank(scope, list_id, word_id):
        word_id = int(word_id)
        if scope == 'template':
            tpl = AdminModel.load_template()
            before = len(tpl['words'])
            tpl['words'] = [w for w in tpl['words'] if int(w.get('id', -1)) != word_id]
            AdminModel.save_template(tpl)
            return len(tpl['words']) < before
        if scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            return WordModel.delete_word(uid, word_id)
        raise ValueError("无效的词库管理范围")

    @staticmethod
    def broadcast_existing_bank(scope, list_id):
        list_id = int(list_id)
        if scope == 'template':
            tpl = AdminModel.load_template()
            target = next((l for l in tpl['lists'] if int(l.get('id', -1)) == list_id), None)
            if not target:
                raise ValueError("模板词库单元不存在")
            words = [w for w in tpl['words'] if int(w.get('list_id', -1)) == list_id]
            return AdminModel.broadcast_list_to_all_students(target['name'], target.get('description', ''), words)
        if scope.startswith('user:'):
            uid = int(scope.split(':', 1)[1])
            lists = VocabListModel.get_all_lists(uid)
            target = next((l for l in lists if int(l['id']) == list_id), None)
            if not target:
                raise ValueError("词库单元不存在")
            words = WordModel.get_words_by_list(uid, list_id)
            return AdminModel.broadcast_list_to_all_students(target['name'], target.get('description', ''), words)
        raise ValueError("无效的词库管理范围")
