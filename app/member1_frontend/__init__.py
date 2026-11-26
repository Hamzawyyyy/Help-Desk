"""Member 1 — Frontend & Team Lead.

Member 1's own pages and helpers live in this folder. The shared layout files
(app/templates/base.html, index.html, auth pages, app/static) are also styled by
Member 1. app/__init__.py calls init_app(app) once to switch the folder on.
"""
from flask import Blueprint, current_app

bp = Blueprint("member1_frontend", __name__, template_folder="templates")


@bp.app_template_global()
def has_endpoint(name):
    """Lets the menu show a link only when that member's page exists."""
    return name in current_app.view_functions


def init_app(app):
    app.register_blueprint(bp)