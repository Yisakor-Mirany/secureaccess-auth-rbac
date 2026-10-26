"""Authorization / RBAC: who can reach which endpoint."""
from .conftest import ADMIN_PASSWORD

PROTECTED = ["/dashboard", "/api/me", "/admin", "/api/admin/users"]


def test_home_is_public(client):
    assert client.get("/").status_code == 200


def test_unauthenticated_gets_401_everywhere(client):
    for url in PROTECTED:
        assert client.get(url).status_code == 401, url


def test_user_can_access_user_dashboard(auth, client):
    auth.register()
    auth.login()
    assert client.get("/dashboard").status_code == 200
    me = client.get("/api/me").get_json()
    assert me["username"] == "alice" and me["role"] == "User"
    assert "password_hash" not in me


def test_user_denied_admin_dashboard_403(auth, client):
    auth.register()
    auth.login()
    assert client.get("/admin").status_code == 403
    assert client.get("/api/admin/users").status_code == 403


def test_admin_can_access_both_dashboards(auth, client, admin_user):
    auth.register()  # a normal user to show up in the list
    assert auth.login(admin_user, ADMIN_PASSWORD).status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.get("/admin").status_code == 200
    data = client.get("/api/admin/users").get_json()
    usernames = {u["username"] for u in data["users"]}
    assert {"alice", admin_user} <= usernames


def test_admin_views_never_expose_password_hashes(auth, client, admin_user):
    auth.register()
    auth.login(admin_user, ADMIN_PASSWORD)
    for url in ("/admin", "/api/admin/users"):
        body = client.get(url).get_data(as_text=True)
        assert "argon2" not in body and "password_hash" not in body, url


def test_demoted_admin_loses_access_immediately(app, auth, client, admin_user):
    """Role is re-read from the database on each request, not cached in the session."""
    from app.db import get_db
    auth.login(admin_user, ADMIN_PASSWORD)
    assert client.get("/admin").status_code == 200
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET role = 'User' WHERE username = ?", (admin_user,))
        db.commit()
    assert client.get("/admin").status_code == 403


def test_create_admin_rejects_weak_password(app):
    result = app.test_cli_runner().invoke(args=["create-admin"], input="admin2\nshort\nshort\n")
    assert result.exit_code != 0
    assert "at least 12" in result.output
