"""Member 2 — Authentication & Roles.

Everything Member 2 adds lives in this folder. app/__init__.py calls
init_app(app) once to switch the folder on.
"""
from flask import Blueprint

bp = Blueprint("member2_auth", __name__, template_folder="templates")


def init_app(app):
    from . import routes  # noqa: F401  (adds the pages to bp)
    app.register_blueprint(bp)