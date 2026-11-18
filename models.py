import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from config import BASE_DIR
from database import db_cursor


def _load_starter_seed():
    seed_path = os.path.join(BASE_DIR, 'docs', 'data', 'vocab.json')
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
            cur.execute("SELECT id, email, username, created_at FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None

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

            return {'id': new_user_id, 'username': username, 'email': email}

    @staticmethod
    def authenticate(identifier, password):
        identifier = (identifier or '').strip()
        password = password or ''
        if not identifier or not password:
            return None

        with db_cursor(commit=False) as cur:
            cur.execute(
                """SELECT id, email, username, password_hash
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

            if check_password_hash(stored_hash, password):
                return {'id': row['id'], 'username': row['username'], 'email': row['email']}
            return None


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
