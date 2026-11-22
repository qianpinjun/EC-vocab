import os
from security import load_or_create_private_secret

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(DATA_DIR, 'ec_words.db'))

# Cryptographic session secret: read from SECRET_KEY env var or lazily created in private data/.secret_key
SECRET_KEY = load_or_create_private_secret(DATA_DIR, '.secret_key', 'SECRET_KEY', length_bytes=32)

PORT = int(os.environ.get('PORT', 5000))
HOST = os.environ.get('HOST', '0.0.0.0')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# School Admin credentials: NEVER hardcoded in public source code.
# Set ADMIN_PASSWORD env var in production, or read the auto-generated bootstrap secret in data/.admin_password.
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin').strip() or 'admin'
ADMIN_PASSWORD_FROM_ENV = bool((os.environ.get('ADMIN_PASSWORD') or '').strip())
ADMIN_PASSWORD = load_or_create_private_secret(DATA_DIR, '.admin_password', 'ADMIN_PASSWORD', length_bytes=14)
