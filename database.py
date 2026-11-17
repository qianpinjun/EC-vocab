import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH

def get_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
        # Users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                coins INTEGER DEFAULT 50,
                words_mastered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

        # Pets table
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

        # Ensure default user (id=1) exists for single-user / no-login mode
        cur.execute("""
            INSERT OR IGNORE INTO users (id, email, username, password_hash)
            VALUES (1, 'default@local', 'default', '')
        """)

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
