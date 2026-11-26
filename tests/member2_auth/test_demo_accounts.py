"""Member 2 — tests for the seed-demo and set-role commands."""
from app import db
from app.models import User
from test_tickets import users  # noqa: F401  (shared fixture from Member 3's tests)


def role_of(app, username):
    with app.app_context():
        db.session.remove()
        return db.session.scalar(db.select(User.role).where(User.username == username))


def test_seed_demo_creates_accounts(app):
    result = app.test_cli_runner().invoke(args=["seed-demo", "--password", "demo-pass-123"])
    assert result.exit_code == 0, result.output
    with app.app_context():
        accounts = {u.email: u for u in db.session.scalars(db.select(User)).all()}
        assert accounts["admin@demo.test"].role == "admin"
        assert accounts["support@demo.test"].role == "support"
        assert accounts["user1@demo.test"].role == "user"
        assert accounts["user2@demo.test"].role == "user"
        assert accounts["admin@demo.test"].check_password("demo-pass-123")


def test_seed_demo_is_safe_to_run_twice(app):
    runner = app.test_cli_runner()
    runner.invoke(args=["seed-demo", "--password", "first-password"])
    result = runner.invoke(args=["seed-demo", "--password", "second-password"])
    assert result.exit_code == 0 and "Reset admin@demo.test" in result.output
    with app.app_context():
        assert db.session.query(User).count() == 4
        admin = db.session.scalar(db.select(User).where(User.email == "admin@demo.test"))
        assert admin.check_password("second-password")


def test_seed_demo_rejects_short_password(app):
    result = app.test_cli_runner().invoke(args=["seed-demo", "--password", "short"])
    assert result.exit_code != 0
    with app.app_context():
        assert db.session.query(User).count() == 0


def test_demo_admin_can_log_in(app, client):
    from conftest import post_form
    app.test_cli_runner().invoke(args=["seed-demo", "--password", "demo-pass-123"])
    response = post_form(client, "/auth/login", {"email": "admin@demo.test", "password": "demo-pass-123"})
    assert response.status_code == 302
    assert client.get("/admin/users").status_code == 200


def test_set_role_command(app, users):
    result = app.test_cli_runner().invoke(args=["set-role", "Owner@Example.test", "support"])
    assert result.exit_code == 0 and "owner is now support" in result.output
    assert role_of(app, "owner") == "support"


def test_set_role_unknown_email_fails(app, users):
    result = app.test_cli_runner().invoke(args=["set-role", "nobody@example.test", "admin"])
    assert result.exit_code != 0 and "No account" in result.output


def test_set_role_rejects_unknown_role(app, users):
    result = app.test_cli_runner().invoke(args=["set-role", "owner@example.test", "superuser"])
    assert result.exit_code != 0
    assert role_of(app, "owner") == "user"