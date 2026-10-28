"""SecureAccess application factory."""

import os

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

from . import cli, db
from .config import Config
from .extensions import csrf, limiter, server_session


PLACEHOLDER_SECRET = "replace-me-with-a-long-random-value"


# Friendly, fixed messages.
# Internal error details are never sent to users.
ERROR_MESSAGES = {
    400: "The request was invalid.",
    401: "You must log in to access this page.",
    403: "You do not have permission to access this page.",
    404: "Page not found.",
    405: "Method not allowed.",
    413: "Request too large.",
    429: "Too many attempts. Please wait a moment and try again.",
    500: "Something went wrong. Please try again later.",
}


def create_app(test_config: dict | None = None) -> Flask:
    """
    Create and configure the SecureAccess Flask application.

    Security features:
    - Argon2id password hashing (handled by authentication module)
    - Server-side session authentication
    - SQLite-backed session storage
    - CSRF protection
    - Login rate limiting
    - Server-side role-based authorization
    - Secure HTTP response headers
    """

    app = Flask(__name__, instance_relative_config=True)

    # --------------------------------------------------
    # 1. Load application configuration
    # --------------------------------------------------

    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # --------------------------------------------------
    # 2. Validate application secret key
    # --------------------------------------------------

    secret = app.config.get("SECRET_KEY")

    if not secret or secret == PLACEHOLDER_SECRET:
        raise RuntimeError(
            "SECRET_KEY is not set. "
            "Copy .env.example to .env and set a random SECRET_KEY."
        )

    # --------------------------------------------------
    # 3. Initialize application database directory
    # --------------------------------------------------

    os.makedirs(
        app.instance_path,
        exist_ok=True
    )

    app.config.setdefault(
        "DATABASE",
        os.path.join(
            app.instance_path,
            app.config["DATABASE_PATH"]
        )
    )

    # --------------------------------------------------
    # 4. F1 SECURITY FIX: SQLite-backed session storage
    # --------------------------------------------------

    # Previously, sessions were stored using FileSystemCache
    # with a threshold of 1000 entries.
    #
    # This could cause legitimate sessions to be evicted
    # when the cache reached its configured capacity.
    #
    # SQLite-backed sessions remove that cache threshold.

    app.config["SESSION_TYPE"] = "sqlalchemy"

    # Use a separate database for server-side sessions.
    # Existing user accounts remain in the original database.

    session_database_path = os.path.join(
        app.instance_path,
        "sessions.db"
    )

    # IMPORTANT:
    # Use the default session database only when no custom
    # SQLAlchemy database URI has been provided.
    #
    # This allows regression tests to use their own
    # temporary SQLite database instead of writing to
    # the application's normal session database.

    app.config.setdefault(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///" + session_database_path
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Periodically clean up expired sessions.
    app.config["SESSION_CLEANUP_N_REQUESTS"] = 100

    # Initialize SQLAlchemy before Flask-Session.
    session_db = SQLAlchemy(app)

    app.config["SESSION_SQLALCHEMY"] = session_db

    # --------------------------------------------------
    # 5. Initialize security extensions
    # --------------------------------------------------

    # CSRF protection
    csrf.init_app(app)

    # Database-backed server-side sessions
    server_session.init_app(app)

    # Request rate limiting
    limiter.init_app(app)

    # Existing SQLite user database
    db.init_app(app)

    # Command-line utilities
    cli.init_app(app)

    # --------------------------------------------------
    # 6. Register application routes
    # --------------------------------------------------

    from . import auth, routes

    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)

    # --------------------------------------------------
    # 7. Register security middleware
    # --------------------------------------------------

    _register_security_headers(app)
    _register_error_handlers(app)

    return app


def _register_security_headers(app: Flask) -> None:
    """
    Add security-related HTTP response headers.
    """

    @app.after_request
    def set_headers(response):

        # Content Security Policy:
        # Only allow resources from the application's origin.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )

        # Prevent MIME-type sniffing.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking.
        response.headers["X-Frame-Options"] = "DENY"

        # Restrict referrer information.
        response.headers["Referrer-Policy"] = "same-origin"

        # Prevent caching of authenticated pages.
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"

        # Enable HSTS when HTTPS-only cookies are configured.
        if app.config["SESSION_COOKIE_SECURE"]:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


def _wants_json() -> bool:
    """
    Determine whether the request expects a JSON response.
    """

    return (
        request.path.startswith("/api/")
        or request.is_json
        or request.method != "GET"
    )


def _error_response(
    status: int,
    message: str | None = None
):
    """
    Return a safe error response without exposing
    internal application details.
    """

    message = message or ERROR_MESSAGES.get(
        status,
        ERROR_MESSAGES[500]
    )

    if _wants_json():
        return jsonify(error=message), status

    return render_template(
        "error.html",
        status=status,
        message=message
    ), status


def _register_error_handlers(app: Flask) -> None:
    """
    Register application-wide error handlers.
    """

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_e):

        return _error_response(
            400,
            "Security token missing or invalid. "
            "Refresh the page and try again."
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(e):

        # Only expose explicitly approved error descriptions.
        message = (
            e.description
            if e.code == 400
            else None
        )

        return _error_response(
            e.code or 500,
            message
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):

        # Log internal errors on the server only.
        app.logger.exception(
            "Unhandled exception"
        )

        # Never expose stack traces to users.
        return _error_response(500)