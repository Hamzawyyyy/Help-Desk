"""Member 2 — reusable role checks, so every feature checks roles the same way."""
from functools import wraps
from flask import abort
from flask_login import current_user, login_required

ROLES = ("user", "support", "admin")
STAFF_ROLES = ("support", "admin")


def is_staff(user):
    """Support agents and admins can see and manage every ticket."""
    return user.is_authenticated and user.role in STAFF_ROLES


def role_required(*roles):
    """Decorator: the logged-in user must have one of the given roles, else 403."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


admin_required = role_required("admin")