import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash
from config import DATABASE_PATH, ADMIN_USERNAME, ADMIN_PASSWORD


def get_db():
    conn = sqlite3.connect(DATABASE_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def db_cursor(commit=True):
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db_cursor() as cur:
        # Enable WAL mode for safe multi-student concurrent access on a server
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")

        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_disabled INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 50,
                words_mastered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for col_sql in (
            "ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN is_disabled INTEGER DEFAULT 0",
        ):
            try:
                cur.execute(col_sql)
            except sqlite3.OperationalError:
                pass

        # Vocab Lists table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vocab_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        try:
            cur.execute("ALTER TABLE vocab_lists ADD COLUMN sort_order INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Words table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                meaning TEXT NOT NULL,
                phonetic TEXT DEFAULT '',
                example_en TEXT DEFAULT '',
                example_cn TEXT DEFAULT '',
                wrong_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                mastered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (list_id) REFERENCES vocab_lists (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Per-user cumulative study statistics (powers the online school ranking system)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                vocab_reviewed INTEGER DEFAULT 0,
                vocab_correct INTEGER DEFAULT 0,
                grammar_completed INTEGER DEFAULT 0,
                grammar_correct INTEGER DEFAULT 0,
                last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Per-question grammar attempt log (tracks unique grammar questions gone through + accuracy)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grammar_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                topic_id TEXT DEFAULT '',
                is_correct INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_grammar_attempts_user ON grammar_attempts (user_id, question_id)")

        # Pets table (legacy compatibility)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                name TEXT DEFAULT '旺财',
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                hunger INTEGER DEFAULT 80,
                happiness INTEGER DEFAULT 80,
                hat TEXT DEFAULT 'none',
                glasses TEXT DEFAULT 'none',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Mistake logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mistake_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                list_id INTEGER,
                word TEXT NOT NULL,
                correct_meaning TEXT NOT NULL,
                chosen_wrong_word TEXT NOT NULL,
                chosen_wrong_meaning TEXT NOT NULL,
                context_question TEXT DEFAULT '',
                round_number INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Quiz history records table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                list_id INTEGER NOT NULL,
                rounds_count INTEGER DEFAULT 1,
                total_mistakes INTEGER DEFAULT 0,
                coins_earned INTEGER DEFAULT 0,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Ensure default local seed user (id=1) exists
        cur.execute("""
            INSERT OR IGNORE INTO users (id, email, username, password_hash)
            VALUES (1, 'default@local', 'default', '')
        """)

        # Ensure dedicated school Admin account exists with configured credentials
        admin_uname = (ADMIN_USERNAME or 'admin').strip()
        admin_email = f"{admin_uname.lower()}@school.admin"
        admin_pw_hash = generate_password_hash(ADMIN_PASSWORD)
        cur.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (admin_uname,))
        admin_row = cur.fetchone()
        if not admin_row:
            cur.execute(
                "INSERT INTO users (email, username, password_hash, is_admin, is_disabled) VALUES (?, ?, ?, 1, 0)",
                (admin_email, admin_uname, admin_pw_hash)
            )
        else:
            cur.execute(
                "UPDATE users SET password_hash = ?, is_admin = 1, is_disabled = 0 WHERE id = ?",
                (admin_pw_hash, admin_row['id'])
            )

        # Backfill user_stats rows for any existing registered users
        cur.execute("""
            INSERT OR IGNORE INTO user_stats (user_id, vocab_reviewed, vocab_correct, grammar_completed, grammar_correct)
            SELECT u.id,
                   COALESCE((SELECT SUM(w.correct_count + w.wrong_count) FROM words w WHERE w.user_id = u.id), 0),
                   COALESCE((SELECT SUM(w.correct_count) FROM words w WHERE w.user_id = u.id), 0),
                   0,
                   0
            FROM users u
        """)


if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
