"""Authentication: registration, login, logout, sessions, CSRF, rate limiting."""
from app.db import get_db
from .conftest import USER_PASSWORD, AuthActions


def test_register_success(auth, app):
    resp = auth.register()
    assert resp.status_code == 201
    with app.app_context():
        row = get_db().execute("SELECT * FROM users WHERE username = 'alice'").fetchone()
    assert row["role"] == "User"
    # Stored as an Argon2id hash, never as plaintext.
    assert row["password_hash"].startswith("$argon2id$")
    assert USER_PASSWORD not in row["password_hash"]


def test_register_cannot_choose_admin_role(auth, app):
    resp = auth.register(username="sneaky", role="Admin")
    assert resp.status_code == 201
    with app.app_context():
        role = get_db().execute("SELECT role FROM users WHERE username = 'sneaky'").fetchone()[0]
    assert role == "User"


def test_register_duplicate_username_case_insensitive(auth):
    assert auth.register(username="alice").status_code == 201
    assert auth.register(username="ALICE").status_code == 409


def test_register_response_has_no_secrets(auth):
    body = auth.register().get_data(as_text=True)
    assert "argon2" not in body and USER_PASSWORD not in body


def test_login_success(auth, client):
    auth.register()
    resp = auth.login()
    assert resp.status_code == 200
    assert "password" not in resp.get_data(as_text=True).lower()
    assert client.get("/dashboard").status_code == 200


def test_login_wrong_password_rejected(auth, client):
    auth.register()
    resp = auth.login(password="wrong-password-123")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid username or password."
    assert client.get("/dashboard").status_code == 401


def test_login_unknown_user_gets_same_message(auth):
    resp = auth.login(username="nobody")
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid username or password."


def test_logout(auth, client):
    auth.register()
    auth.login()
    assert client.get("/dashboard").status_code == 200
    assert auth.logout().status_code == 200
    assert client.get("/dashboard").status_code == 401
    assert client.get("/api/me").status_code == 401


def test_logout_invalidates_session_server_side(app, auth, client):
    """A copied session cookie must stop working after logout."""
    auth.register()
    auth.login()
    stolen = client.get_cookie("secureaccess_session").value
    auth.logout()

    attacker = app.test_client()
    attacker.set_cookie("secureaccess_session", stolen)
    assert attacker.get("/dashboard").status_code == 401


def test_session_id_changes_on_login(auth, client):
    """Session fixation defense: the pre-login session ID is discarded."""
    auth.register()
    client.get("/login")
    before = client.get_cookie("secureaccess_session").value
    auth.login()
    after = client.get_cookie("secureaccess_session").value
    assert before != after


def test_session_cookie_flags(auth, client):
    auth.register()
    resp = auth.login()
    cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_post_without_csrf_token_rejected(client):
    resp = client.post("/login", json={"username": "a", "password": "b"})
    assert resp.status_code == 400
    resp = client.post("/register", json={"username": "abc", "password": USER_PASSWORD})
    assert resp.status_code == 400


def test_logout_requires_post(auth, client):
    auth.register()
    auth.login()
    assert client.get("/logout").status_code == 405
    assert client.get("/dashboard").status_code == 200


def test_login_rate_limit(rate_limited_app):
    auth = AuthActions(rate_limited_app.test_client())
    codes = [auth.login(username="victim", password="guess-number-%d" % i).status_code
             for i in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_security_headers(client):
    resp = client.get("/")
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Cache-Control"] == "no-store"


def test_debug_disabled_by_default(app):
    assert app.debug is False
