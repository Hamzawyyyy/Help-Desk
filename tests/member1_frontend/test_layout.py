"""Member 1 — tests for the menu, layout and restyled pages."""
from conftest import post_form
from test_tickets import users, login  # noqa: F401  (shared fixtures from Member 3's tests)


def test_menu_for_logged_out_visitor(client):
    page = client.get("/").data
    assert b"Log in" in page and b"Register" in page
    assert b"Log out" not in page and b"Create ticket" not in page


def test_menu_for_regular_user(client, users):
    login(client, "owner")
    page = client.get("/").data
    assert b"Tickets" in page and b"Create ticket" in page and b"Log out" in page
    assert b"owner" in page
    assert b"/admin/users" not in page


def test_menu_shows_users_link_only_to_admin(client, app, users):
    login(client, "admin")
    page = client.get("/").data
    if "member2_auth.list_users" in app.view_functions:
        assert b"/admin/users" in page
    else:
        assert b"/admin/users" not in page


def test_menu_shows_role_badge(client, users):
    login(client, "agent")
    assert b"support</span>" in client.get("/tickets").data


def test_logout_button_works(client, users):
    login(client, "owner")
    response = post_form(client, "/auth/logout")
    assert response.status_code == 302
    assert b"Log in" in client.get("/").data


def test_login_and_register_pages_keep_their_fields(client):
    login_page = client.get("/auth/login").data
    for field in (b'name="email"', b'name="password"', b'name="csrf_token"'):
        assert field in login_page
    register_page = client.get("/auth/register").data
    for field in (b'name="username"', b'name="email"', b'name="password"', b'name="csrf_token"'):
        assert field in register_page


def test_register_keeps_typed_values_after_error(client):
    response = post_form(client, "/auth/register", {"username": "ab", "email": "keep@example.test",
                                                    "password": "long-enough-1"})
    assert response.status_code == 400
    assert b'value="keep@example.test"' in response.data


def test_flash_messages_can_be_closed(client, users):
    response = post_form(client, "/auth/login", {"email": "owner@example.test", "password": "wrong"})
    assert b"btn-close" in response.data and b"Invalid email or password" in response.data


def test_page_has_bootstrap_script_and_no_favicon_request(client):
    page = client.get("/").data
    assert b'rel="icon"' in page
    assert b"bootstrap.bundle.min.js" in page