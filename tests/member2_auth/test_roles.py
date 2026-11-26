"""Member 2 — tests for the admin users page and role rules."""
import pytest
from app import db
from app.models import User
from conftest import post_form
from test_tickets import users, login  # noqa: F401  (shared fixtures from Member 3's tests)


def role_of(app, username):
    with app.app_context():
        db.session.remove()
        return db.session.scalar(db.select(User.role).where(User.username == username))


def test_admin_sees_users_page(client, users):
    login(client, "admin")
    page = client.get("/admin/users")
    assert page.status_code == 200
    assert b"owner@example.test" in page.data and b"agent@example.test" in page.data


@pytest.mark.parametrize("actor", ["owner", "agent"])
def test_non_admins_cannot_open_users_page(client, users, actor):
    login(client, actor)
    assert client.get("/admin/users").status_code == 403


def test_anonymous_is_sent_to_login(client):
    response = client.get("/admin/users")
    assert response.status_code == 302 and "/auth/login" in response.location


def test_admin_can_promote_user_to_support(client, app, users):
    login(client, "admin")
    response = post_form(client, f"/admin/users/{users['owner']}/role", {"role": "support"})
    assert response.status_code == 302
    assert role_of(app, "owner") == "support"
    assert b"owner is now support" in client.get(response.location).data


def test_admin_can_demote_support_to_user(client, app, users):
    login(client, "admin")
    post_form(client, f"/admin/users/{users['agent']}/role", {"role": "user"})
    assert role_of(app, "agent") == "user"


def test_invalid_role_is_rejected(client, app, users):
    login(client, "admin")
    response = post_form(client, f"/admin/users/{users['owner']}/role", {"role": "superuser"})
    assert role_of(app, "owner") == "user"
    assert b"Choose a valid role" in client.get(response.location).data


def test_admin_cannot_change_own_role(client, app, users):
    login(client, "admin")
    post_form(client, f"/admin/users/{users['admin']}/role", {"role": "user"})
    assert role_of(app, "admin") == "admin"


def test_support_cannot_change_roles(client, app, users):
    login(client, "agent")
    response = post_form(client, f"/admin/users/{users['owner']}/role", {"role": "admin"})
    assert response.status_code == 403
    assert role_of(app, "owner") == "user"


def test_changing_role_of_missing_user_is_404(client, users):
    login(client, "admin")
    assert post_form(client, "/admin/users/99999/role", {"role": "user"}).status_code == 404


def test_role_change_requires_csrf_token(client, app, users):
    login(client, "admin")
    response = client.post(f"/admin/users/{users['owner']}/role", data={"role": "admin"})
    assert response.status_code == 400
    assert role_of(app, "owner") == "user"


def test_promoted_support_agent_sees_all_tickets(client, app, users):
    login(client, "admin")
    post_form(client, f"/admin/users/{users['other']}/role", {"role": "support"})
    post_form(client, "/auth/logout")
    login(client, "other")
    page = client.get("/tickets")
    assert page.status_code == 200 and b"All support tickets" in page.data