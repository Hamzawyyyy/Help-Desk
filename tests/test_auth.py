import pytest
from app import db
from app.models import User
from conftest import post_form


def register(client, **overrides):
    data = {"username": "student", "email": "student@example.test", "password": "test-password"}
    return post_form(client, "/auth/register", {**data, **overrides})


def test_register_login_logout(client, app):
    assert register(client, role="admin").status_code == 302
    with app.app_context():
        user = db.session.scalar(db.select(User))
        assert user.role == "user"
        assert user.password_hash != "test-password"
        assert user.check_password("test-password")
    response = post_form(client, "/auth/login", {"email": "STUDENT@example.test", "password": "test-password"})
    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session["_user_id"]
    assert post_form(client, "/auth/logout").status_code == 302
    with client.session_transaction() as session:
        assert "_user_id" not in session


@pytest.mark.parametrize("overrides", [
    {"username": "x"}, {"email": "invalid"}, {"password": "short"},
    {"password": "x" * 129}, {"username": "<script>"},
])
def test_invalid_registration(client, app, overrides):
    assert register(client, **overrides).status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 0


def test_duplicate_registration_and_bad_login(client, app):
    register(client)
    assert register(client).status_code == 400
    assert post_form(client, "/auth/login", {"email": "student@example.test", "password": "wrong"}).status_code == 400
    assert post_form(client, "/auth/login", {"email": "missing@example.test", "password": "wrong"}).status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(User.id))) == 1


def test_csrf_required(client):
    assert client.post("/auth/register", data={}).status_code == 400
    assert client.post("/auth/login", data={"csrf_token": "wrong"}).status_code == 400
    assert client.get("/auth/logout").status_code == 405


def test_init_db_command(app):
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0
    assert "Database tables created" in result.output
