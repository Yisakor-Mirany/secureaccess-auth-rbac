"""Application settings, read from environment variables.

Secrets never live in source code. python-dotenv copies values from the
local .env file into the environment, and this module reads them from there.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DEBUG = _env_flag("FLASK_DEBUG")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "secureaccess.db")

    # --- Session cookie ---------------------------------------------------
    # The cookie only holds a random session ID; the data lives server-side.
    SESSION_COOKIE_NAME = "secureaccess_session"
    SESSION_COOKIE_HTTPONLY = True      # JavaScript cannot read the cookie (limits XSS damage)
    SESSION_COOKIE_SAMESITE = "Lax"     # Not sent on cross-site POSTs (defense in depth for CSRF)
    SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE")  # Must be True in HTTPS production
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
    )

    # --- Flask-Session (server-side storage) ---------------------------------
    SESSION_TYPE = "sqlalchemy"          # SESSION_CACHELIB is built in create_app()
    SESSION_CLEANUP_N_REQUESTS = 100
    SESSION_PERMANENT = True

    # --- CSRF (Flask-WTF) -----------------------------------------------------
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None          # Token lives as long as the session itself

    # --- Rate limiting (Flask-Limiter) ---------------------------------------
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = "memory://"
    LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5 per minute;20 per hour")

    # Reject request bodies larger than 16 KB (forms here are tiny).
    MAX_CONTENT_LENGTH = 16 * 1024
