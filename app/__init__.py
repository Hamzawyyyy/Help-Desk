import secrets
import hmac
import click
from flask import Flask, render_template, session, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(CSRF_ENABLED=True, MAX_CONTENT_LENGTH=1024 * 1024,
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    login_manager.init_app(app)

    @app.context_processor
    def csrf_context():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        return {"csrf_token": session["csrf_token"]}

    @app.before_request
    def protect_forms():
        if app.config["CSRF_ENABLED"] and request.method == "POST":
            expected = session.get("csrf_token", "")
            supplied = request.form.get("csrf_token", "")
            if not expected or not hmac.compare_digest(expected, supplied):
                abort(400, description="Invalid form token. Reload the page and try again.")

    from app.routes.auth import auth
    app.register_blueprint(auth)
    from app.routes.tickets import tickets
    app.register_blueprint(tickets)

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables without deleting existing data."""
        db.create_all()
        click.echo("Database tables created.")

    @app.get("/")
    def home():
        return render_template("index.html")

    return app
