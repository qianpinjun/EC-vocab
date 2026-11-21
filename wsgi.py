"""Production WSGI entrypoint for Gunicorn (Linux) or Waitress (Windows/Cross-platform)."""
from database import init_db
from app import app as application

init_db()

if __name__ == "__main__":
    from config import HOST, PORT
    try:
        from waitress import serve
        print(f"Serving EC Language Lab via Waitress on http://{HOST}:{PORT}")
        serve(application, host=HOST, port=PORT, threads=8)
    except ImportError:
        application.run(host=HOST, port=PORT, debug=False)
