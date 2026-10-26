"""Server-side input validation.

The browser also validates (for a friendlier experience), but anyone can skip
the browser and send requests with curl, so the server is the real gatekeeper.
"""
import re

USERNAME_MIN, USERNAME_MAX = 3, 30
PASSWORD_MIN, PASSWORD_MAX = 12, 128   # Upper bound stops huge inputs from tying up the hasher

# Allow-list: letters, digits, underscore, dot, hyphen. Anything else is rejected.
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def validate_username(username) -> str | None:
    """Return an error message, or None if the username is acceptable."""
    if not isinstance(username, str) or not username.strip():
        return "Username is required."
    if not USERNAME_MIN <= len(username) <= USERNAME_MAX:
        return f"Username must be {USERNAME_MIN}-{USERNAME_MAX} characters."
    if not USERNAME_RE.fullmatch(username):
        return "Username may only contain letters, numbers, '.', '_' and '-'."
    return None


def validate_password(password) -> str | None:
    """Return an error message, or None if the password is acceptable.

    Any characters are allowed (spaces, symbols, emoji) - passwords are hashed,
    never displayed or placed into SQL, so there is nothing to "sanitize".
    """
    if not isinstance(password, str) or password == "":
        return "Password is required."
    if len(password) < PASSWORD_MIN:
        return f"Password must be at least {PASSWORD_MIN} characters."
    if len(password) > PASSWORD_MAX:
        return f"Password must be at most {PASSWORD_MAX} characters."
    return None
