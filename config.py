import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(DATA_DIR, 'ec_words.db'))


def _load_or_create_secret_key():
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    key_file = os.path.join(DATA_DIR, '.secret_key')
    try:
        if os.path.exists(key_file):
            with open(key_file, 'r', encoding='utf-8') as f:
                val = f.read().strip()
                if len(val) >= 24:
                    return val
        new_key = secrets.token_hex(32)
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(new_key)
        return new_key
    except Exception:
        return 'ec-school-studio-fallback-secret-key-2026'


SECRET_KEY = _load_or_create_secret_key()
PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'ec2026')
