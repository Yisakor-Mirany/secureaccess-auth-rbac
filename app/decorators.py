"""Authorization decorators - the heart of RBAC in this app.

    @login_required          -> 401 Unauthorized if nobody is logged in
    @role_required("Admin")  -> 401 if not logged in, 403 Forbidden if wrong role

g.user is loaded fresh from the database on every request (see auth.py), so
the role checked here is always the *current* role, not a stale copy.
"""
from functools import wraps

from flask import abort, g


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            abort(401)
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.get("user") is None:
                abort(401)
            if g.user["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
