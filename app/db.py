"""SQLite helpers.

Every query in this project uses "?" placeholders (parameterized queries).
The database driver sends values separately from the SQL text, so user input
can never change the structure of a query - this is what stops SQL injection.
"""
import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db() -> sqlite3.Connection:
    """Return one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Create tables if they do not exist yet (safe to run repeatedly)."""
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    get_db().executescript(schema)


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """Create the database tables."""
    init_db()
    click.echo(f"Database ready at {current_app.config['DATABASE']}")


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    with app.app_context():
        init_db()
