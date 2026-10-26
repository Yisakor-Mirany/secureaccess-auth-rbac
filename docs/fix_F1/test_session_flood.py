"""Regression test for audit finding F1 (anonymous requests evicting logged-in sessions)."""
import time

from cachelib.file import FileSystemCache

from app import create_app
from .conftest import AuthActions


def test_anonymous_flood_does_not_log_out_users(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE": str(tmp_path / "test.db"),
        # Used by the ORIGINAL file-cache backend: a tiny store so a few requests overflow it.
        "SESSION_CACHELIB": FileSystemCache(str(tmp_path / "sessions"), threshold=20),
        # Used by the FIXED database backend.
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "sessions.db"),
        "RATELIMIT_ENABLED": False,
    })
    victim = app.test_client()
    auth = AuthActions(victim)
    auth.register("victim", "victim-password-1")
    auth.login("victim", "victim-password-1")
    assert victim.get("/dashboard").status_code == 200

    # Session expiry has 1-second resolution; wait so the victim's session is
    # strictly the oldest - the first one a size-limited store would evict.
    time.sleep(1.1)
    for _ in range(30):
        app.test_client().get("/login")   # brand-new client = no cookies = new anonymous session

    assert victim.get("/dashboard").status_code == 200
