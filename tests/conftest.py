"""Shared test fixtures.

Each test gets a fresh temporary database and session store. CSRF protection
stays ENABLED, so the helpers fetch a real token first, just like the browser.
"""
import re

import pytest
from cachelib.file import FileSystemCache

from app import create_app
from app.extensions import limiter

USER_PASSWORD = "correct-horse-battery"
ADMIN_PASSWORD = "admin-passphrase-123"


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE": str(tmp_path / "test.db"),
        "SESSION_CACHELIB": FileSystemCache(str(tmp_path / "sessions")),
        "RATELIMIT_ENABLED": False,
    })
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def get_csrf_token(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html)
    assert match, "CSRF meta tag not found"
    return match.group(1)


class AuthActions:
    def __init__(self, client):
        self.client = client

    def post(self, url, payload=None, token_page="/login"):
        token = get_csrf_token(self.client, token_page)
        return self.client.post(url, json=payload or {}, headers={"X-CSRFToken": token})

    def register(self, username="alice", password=USER_PASSWORD, **extra):
        return self.post("/register", {"username": username, "password": password, **extra})

    def login(self, username="alice", password=USER_PASSWORD):
        return self.post("/login", {"username": username, "password": password})

    def logout(self):
        return self.post("/logout", token_page="/")


@pytest.fixture
def auth(client):
    return AuthActions(client)


@pytest.fixture
def admin_user(app):
    """Create an Admin through the real CLI command (the only supported way)."""
    result = app.test_cli_runner().invoke(
        args=["create-admin"], input=f"root_admin\n{ADMIN_PASSWORD}\n{ADMIN_PASSWORD}\n"
    )
    assert result.exit_code == 0, result.output
    return "root_admin"


@pytest.fixture
def rate_limited_app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
        "DATABASE": str(tmp_path / "test.db"),
        "SESSION_CACHELIB": FileSystemCache(str(tmp_path / "sessions")),
        "RATELIMIT_ENABLED": True,
        "LOGIN_RATE_LIMIT": "5 per minute",
    })
    limiter.reset()
    yield app
    limiter.reset()
