"""Input validation, special characters, and SQL injection attempts."""
from app.db import get_db
from .conftest import USER_PASSWORD


def test_empty_username_rejected(auth):
    assert auth.register(username="").status_code == 400
    assert auth.register(username="   ").status_code == 400
    assert auth.login(username="").status_code == 400


def test_empty_password_rejected(auth):
    assert auth.register(password="").status_code == 400
    assert auth.login(password="").status_code == 400


def test_short_password_rejected(auth):
    resp = auth.register(password="short")
    assert resp.status_code == 400
    assert "12" in resp.get_json()["error"]


def test_missing_fields_and_wrong_types_rejected(auth):
    assert auth.post("/register", {}).status_code == 400
    assert auth.post("/register", {"username": 123, "password": ["x"]}).status_code == 400
    assert auth.post("/login", {"username": None, "password": None}).status_code == 400


def test_non_json_body_rejected(client):
    from .conftest import get_csrf_token
    token = get_csrf_token(client)
    resp = client.post("/login", data="not json", headers={"X-CSRFToken": token,
                                                          "Content-Type": "text/plain"})
    assert resp.status_code == 400


def test_special_characters_in_username_rejected_safely(auth):
    for name in ["<script>alert(1)</script>", "bob smith", "émile", "a/b", "x\"y"]:
        resp = auth.register(username=name)
        assert resp.status_code == 400, name
        assert "<script>" not in resp.get_data(as_text=True)


def test_special_characters_in_password_work(auth, client):
    password = "p@ss w0rd!<>'\";--ünïcødé🔒"
    assert auth.register(username="special", password=password).status_code == 201
    assert auth.login(username="special", password=password).status_code == 200
    assert client.get("/dashboard").status_code == 200


def test_sql_injection_login_does_not_bypass(auth, client):
    auth.register()
    payloads = ["' OR '1'='1", "' OR 1=1 --", "alice' --", "\" OR \"\"=\"", "admin'/*"]
    for payload in payloads:
        resp = auth.login(username=payload, password="' OR '1'='1")
        assert resp.status_code in (400, 401), payload
        assert client.get("/dashboard").status_code == 401, payload


def test_sql_injection_password_field_does_not_bypass(auth, client):
    auth.register()
    resp = auth.login(username="alice", password="' OR '1'='1' --")
    assert resp.status_code == 401
    assert client.get("/dashboard").status_code == 401


def test_sql_injection_does_not_damage_database(auth, app):
    auth.register()
    auth.login(username="x'; DROP TABLE users; --", password=USER_PASSWORD)
    auth.register(username="x'; DROP TABLE users; --")
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]
    assert count == 1


def test_overlong_input_rejected(auth):
    assert auth.register(username="a" * 31).status_code == 400
    assert auth.register(password="a" * 129).status_code == 400
    assert auth.login(username="alice", password="a" * 129).status_code == 401


def test_unknown_api_route_returns_json_404(client):
    resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Page not found."}
