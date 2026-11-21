@echo off
cd /d "%~dp0"
if not exist "venv" (
    echo [1/3] Creating Python virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [2/3] Installing dependencies...
pip install -q -r requirements.txt
echo [3/3] Starting EC Language Lab production server via Waitress on http://0.0.0.0:5000 ...
python wsgi.py
pause
