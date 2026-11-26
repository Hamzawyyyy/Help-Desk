"""Member 2 — command-line helpers for local demos.

    flask --app run seed-demo              create/reset the demo accounts
    flask --app run set-role EMAIL ROLE    give an existing account a role
"""
import click
from flask.cli import with_appcontext
from app import db
from app.models import User
from .permissions import ROLES

DEMO_ACCOUNTS = (
    ("admin", "admin@demo.test", "admin"),
    ("support", "support@demo.test", "support"),
    ("user1", "user1@demo.test", "user"),
    ("user2", "user2@demo.test", "user"),
)


@click.command("seed-demo")
@with_appcontext
@click.option("--password", prompt="Password for all demo accounts", hide_input=True,
              confirmation_prompt=True, help="Password given to every demo account.")
def seed_demo(password):
    """Create or reset local demo accounts (one admin, one support agent, two users)."""
    if not 8 <= len(password) <= 128:
        raise click.BadParameter("Password must contain 8-128 characters.", param_hint="--password")
    for username, email, role in DEMO_ACCOUNTS:
        user = db.session.scalar(db.select(User).where(User.email == email))
        created = user is None
        if created:
            user = User(username=username, email=email)
            db.session.add(user)
        user.role = role
        user.set_password(password)
        click.echo(f"{'Created' if created else 'Reset'} {email} ({role})")
    db.session.commit()
    click.echo("Demo accounts ready. Use them only on your local demo database.")


@click.command("set-role")
@with_appcontext
@click.argument("email")
@click.argument("role", type=click.Choice(ROLES))
def set_role(email, role):
    """Give an existing account the user, support or admin role."""
    user = db.session.scalar(db.select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise click.ClickException(f"No account with email {email}.")
    user.role = role
    db.session.commit()
    click.echo(f"{user.username} is now {role}.")