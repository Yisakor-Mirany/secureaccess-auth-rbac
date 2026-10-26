"""Command-line tools. Admins can ONLY be created here, never via the website.

Usage:  flask --app run create-admin

The password is typed at a hidden prompt, so it never appears on screen,
in shell history, or in the source code.
"""
import sqlite3

import click
from flask.cli import with_appcontext

from .db import get_db
from .passwords import hash_password
from .validation import validate_password, validate_username


@click.command("create-admin")
@with_appcontext
def create_admin_command() -> None:
    """Create a new Admin account interactively."""
    username = click.prompt("Admin username").strip()
    error = validate_username(username)
    if error:
        raise click.ClickException(error)

    password = click.prompt("Admin password", hide_input=True, confirmation_prompt=True)
    error = validate_password(password)
    if error:
        raise click.ClickException(error)

    try:
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'Admin')",
            (username, hash_password(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise click.ClickException(f"User '{username}' already exists.")

    click.echo(f"Admin account '{username}' created.")


def init_app(app) -> None:
    app.cli.add_command(create_admin_command)
