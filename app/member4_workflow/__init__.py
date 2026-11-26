"""Member 4 — Status, Comments & History.

Everything Member 4 adds lives in this folder. app/__init__.py calls
init_app(app) once to switch the folder on.
"""
from flask import Blueprint

bp = Blueprint("member4_workflow", __name__, template_folder="templates")


def init_app(app):
    from . import models, rules, routes  # noqa: F401  (tables, history log, pages)
    app.register_blueprint(bp)