"""Pages and JSON API endpoints, grouped by access level."""
from flask import Blueprint, g, jsonify, render_template

from .db import get_db
from .decorators import login_required, role_required

bp = Blueprint("main", __name__)


def _list_users():
    # Columns are listed explicitly - password_hash is never selected.
    return get_db().execute(
        "SELECT id, username, role, created_at, last_login_at FROM users ORDER BY id"
    ).fetchall()


# --- Public -------------------------------------------------------------
@bp.route("/")
def index():
    return render_template("index.html")


# --- Any authenticated user (User or Admin) -----------------------------
@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=g.user)


@bp.route("/api/me")
@login_required
def api_me():
    return jsonify(dict(g.user))


# --- Admin only -----------------------------------------------------------
@bp.route("/admin")
@role_required("Admin")
def admin_dashboard():
    return render_template("admin.html", users=_list_users())


@bp.route("/api/admin/users")
@role_required("Admin")
def api_admin_users():
    return jsonify(users=[dict(row) for row in _list_users()])
