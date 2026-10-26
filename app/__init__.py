"""SecureAccess application factory."""
import os

from cachelib.file import FileSystemCache
from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException

from . import cli, db
from .config import Config
from .extensions import csrf, limiter, server_session

PLACEHOLDER_SECRET = "replace-me-with-a-long-random-value"

# Friendly, fixed messages - internal error details are never sent to users.
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
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    secret = app.config.get("SECRET_KEY")
    if not secret or secret == PLACEHOLDER_SECRET:
        raise RuntimeError(
            "SECRET_KEY is not set. Copy .env.example to .env and set a random SECRET_KEY."
        )

    os.makedirs(app.instance_path, exist_ok=True)
    app.config.setdefault("DATABASE", os.path.join(app.instance_path, app.config["DATABASE_PATH"]))
    if "SESSION_CACHELIB" not in app.config:
        app.config["SESSION_CACHELIB"] = FileSystemCache(
            os.path.join(app.instance_path, "flask_session"), threshold=1000, mode=0o600
        )

    csrf.init_app(app)
    server_session.init_app(app)
    limiter.init_app(app)
    db.init_app(app)
    cli.init_app(app)

    from . import auth, routes
    app.register_blueprint(auth.bp)
    app.register_blueprint(routes.bp)

    _register_security_headers(app)
    _register_error_handlers(app)
    return app


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def set_headers(response):
        # Only load scripts/styles from our own origin; no inline scripts allowed.
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
            "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if not request.path.startswith("/static/"):
            # Do not let the browser cache pages - after logout, "Back" must not show a dashboard.
            response.headers["Cache-Control"] = "no-store"
        if app.config["SESSION_COOKIE_SECURE"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


def _wants_json() -> bool:
    return request.path.startswith("/api/") or request.is_json or request.method != "GET"


def _error_response(status: int, message: str | None = None):
    message = message or ERROR_MESSAGES.get(status, ERROR_MESSAGES[500])
    if _wants_json():
        return jsonify(error=message), status
    return render_template("error.html", status=status, message=message), status


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(CSRFError)
    def handle_csrf_error(_e):
        return _error_response(400, "Security token missing or invalid. Refresh the page and try again.")

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        # Only 400s we raise ourselves carry a safe, hand-written description.
        message = e.description if e.code == 400 else None
        return _error_response(e.code or 500, message)

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled exception")   # Full details go to the server log only
        return _error_response(500)
