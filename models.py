from database import db_cursor

class VocabListModel:
    @staticmethod
    def get_all_lists():
        """Retrieve all vocabulary lists sorted by defined order"""
        with db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT vl.id, vl.name, vl.description, vl.sort_order, vl.created_at,
                       COUNT(w.id) as word_count
                FROM vocab_lists vl
                LEFT JOIN words w ON vl.id = w.list_id
                GROUP BY vl.id
                ORDER BY vl.sort_order ASC, vl.id ASC
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def create(name, description=''):
        name = name.strip()
        if not name:
            raise ValueError("词库名称不能为空")
        with db_cursor() as cur:
            # Get max sort_order
            cur.execute("SELECT MAX(sort_order) FROM vocab_lists")
            max_order = cur.fetchone()[0] or 0
            cur.execute("""
                INSERT INTO vocab_lists (user_id, name, description, sort_order)
                VALUES (1, ?, ?, ?)
            """, (name, description.strip(), max_order + 1))
            return cur.lastrowid

    @staticmethod
    def delete(list_id):
        with db_cursor() as cur:
            cur.execute("DELETE FROM words WHERE list_id = ?", (list_id,))
            cur.execute("DELETE FROM vocab_lists WHERE id = ?", (list_id,))
            return cur.rowcount > 0

class WordModel:
    @staticmethod
    def get_words_by_list(list_id):
        with db_cursor(commit=False) as cur:
            cur.execute("""
                SELECT id, list_id, word, meaning, phonetic, example_en, example_cn,
                       wrong_count, correct_count, mastered, created_at
                FROM words
                WHERE list_id = ?
                ORDER BY id ASC
            """, (list_id,))
            return [dict(r) for r in cur.fetchall()]

    @staticmethod
    def add_word(list_id, word, meaning, phonetic='', example_en='', example_cn=''):
        word = word.strip()
        meaning = meaning.strip()
        if not word or not meaning:
            raise ValueError("英文单词和中文释义均不能为空")
        with db_cursor() as cur:
            cur.execute("""
                INSERT INTO words (list_id, user_id, word, meaning, phonetic, example_en, example_cn)
                VALUES (?, 1, ?, ?, ?, ?, ?)
            """, (list_id, word, meaning, phonetic.strip(), example_en.strip(), example_cn.strip()))
            return cur.lastrowid

    @staticmethod
    def batch_add_words(list_id, word_items):
        added = 0
        with db_cursor() as cur:
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
                    VALUES (?, 1, ?, ?, ?, ?, ?)
                """, (list_id, w, m, p, een, ecn))
                added += 1
        return added

    @staticmethod
    def delete_word(word_id):
        with db_cursor() as cur:
            cur.execute("DELETE FROM words WHERE id = ?", (word_id,))
            return cur.rowcount > 0

    @staticmethod
    def get_words_by_ids(word_ids):
        clean_ids = [int(wid) for wid in word_ids if wid is not None]
        if not clean_ids:
            return {}
        placeholders = ','.join(['?'] * len(clean_ids))
        with db_cursor(commit=False) as cur:
            cur.execute(f"""
                SELECT id, list_id, word, meaning, phonetic, example_en, example_cn
                FROM words
                WHERE id IN ({placeholders})
            """, clean_ids)
            return {r['id']: dict(r) for r in cur.fetchall()}

    @staticmethod
    def get_extra_random_words(exclude_words, count=2):
        lowered = [w.strip().lower() for w in exclude_words if w and w.strip()]
        with db_cursor(commit=False) as cur:
            if lowered:
                placeholders = ','.join(['?'] * len(lowered))
                where_clause = f"WHERE LOWER(word) NOT IN ({placeholders})"
                params = lowered + [count]
            else:
                where_clause = ""
                params = [count]
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
    def record_answer_stat(word_id, is_correct):
        if not word_id:
            return
        with db_cursor() as cur:
            if is_correct:
                cur.execute("""
                    UPDATE words
                    SET correct_count = correct_count + 1,
                        mastered = CASE WHEN correct_count + 1 >= 2 THEN 1 ELSE mastered END
                    WHERE id = ?
                """, (word_id,))
            else:
                cur.execute("""
                    UPDATE words
                    SET wrong_count = wrong_count + 1,
                        mastered = 0
                    WHERE id = ?
                """, (word_id,))
