#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "[1/3] Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
echo "[2/3] Installing dependencies..."
pip install -q -r requirements.txt

PORT="${PORT:-5000}"
WORKERS="${WORKERS:-4}"
echo "[3/3] Starting EC Language Lab server on http://0.0.0.0:${PORT} (${WORKERS} workers)..."
exec gunicorn --workers "${WORKERS}" --threads 4 --bind "0.0.0.0:${PORT}" --timeout 60 wsgi:application
