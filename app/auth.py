"""Authentication: registration, login, logout, and loading the current user."""
import sqlite3

from flask import (Blueprint, abort, current_app, g, jsonify, redirect,
                   render_template, request, session, url_for)

from .db import get_db
from .extensions import limiter
from .passwords import hash_password, needs_rehash, verify_password
from .validation import PASSWORD_MAX, USERNAME_MAX, validate_password, validate_username

bp = Blueprint("auth", __name__)

GENERIC_LOGIN_ERROR = "Invalid username or password."


@bp.before_app_request
def load_logged_in_user():
    """Look up the logged-in user (if any) from the database on every request.

    Only the user's id is stored in the session. Reading the role from the
    database each time means a demoted or deleted account loses access
    immediately instead of keeping a stale role in its session.
    """
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = get_db().execute(
            "SELECT id, username, role, created_at, last_login_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if g.user is None:          # Account was deleted - drop the orphaned session
            session.clear()


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        abort(400, description="Request body must be a JSON object.")
    return data


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():
    if request.method == "GET":
        if g.user:
            return redirect(url_for("main.dashboard"))
        return render_template("register.html")

    data = _json_body()
    username = data.get("username")
    username = username.strip() if isinstance(username, str) else username
    password = data.get("password")

    error = validate_username(username) or validate_password(password)
    if error:
        return jsonify(error=error), 400

    # NOTE: any "role" field in the request is deliberately ignored.
    # Public registration ALWAYS creates a least-privileged 'User'.
    try:
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'User')",
            (username, hash_password(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="That username is already taken."), 409

    return jsonify(message="Account created. You can now log in."), 201


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config["LOGIN_RATE_LIMIT"], methods=["POST"])
def login():
    if request.method == "GET":
        if g.user:
            return redirect(url_for("main.dashboard"))
        return render_template("login.html")

    data = _json_body()
    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip() \
            or not isinstance(password, str) or password == "":
        return jsonify(error="Username and password are required."), 400

    username = username.strip()
    if len(username) > USERNAME_MAX or len(password) > PASSWORD_MAX:
        return jsonify(error=GENERIC_LOGIN_ERROR), 401

    db = get_db()
    user = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()

    # verify_password() does equal work whether or not the user exists.
    if not verify_password(user["password_hash"] if user else None, password):
        current_app.logger.warning("Failed login for username=%r from %s",
                                   username, request.remote_addr)
        return jsonify(error=GENERIC_LOGIN_ERROR), 401

    if needs_rehash(user["password_hash"]):
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                   (hash_password(password), user["id"]))
    db.execute("UPDATE users SET last_login_at = datetime('now') WHERE id = ?", (user["id"],))
    db.commit()

    # Start a brand-new session with a brand-new ID (prevents session fixation).
    session.clear()
    session["user_id"] = user["id"]
    current_app.session_interface.regenerate(session)

    return jsonify(message="Login successful.", redirect=url_for("main.dashboard")), 200


@bp.route("/logout", methods=["POST"])
def logout():
    # Emptying the session makes Flask-Session delete the server-side record
    # and tell the browser to delete the cookie. A copied cookie is now useless.
    session.clear()
    return jsonify(message="You have been logged out.", redirect=url_for("main.index")), 200
