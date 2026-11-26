"""Member 5 — integration tests: every member's feature working together.

These follow the real demo path through the website, using the demo-account
command, the ticket pages, the status/comment panel, the dashboard and the
admin users page in one story.
"""
import re
from app import db
from app.models import Ticket, User
from conftest import post_form

PASSWORD = "integration-pass-1"


def seed(app):
    result = app.test_cli_runner().invoke(args=["seed-demo", "--password", PASSWORD])
    assert result.exit_code == 0, result.output
    with app.app_context():
        return {u.username: u.id for u in db.session.scalars(db.select(User)).all()}


def log_in_as(client, email):
    post_form(client, "/auth/logout")
    response = post_form(client, "/auth/login", {"email": email, "password": PASSWORD})
    assert response.status_code == 302, "login failed for " + email


def create_ticket(client, title):
    response = post_form(client, "/tickets/new", {
        "title": title, "description": "The office printer shows a paper jam.",
        "category": "Technical", "priority": "High"})
    assert response.status_code == 302
    return int(re.search(r"/tickets/(\d+)", response.location).group(1))


def history(app, ticket_id):
    with app.app_context():
        db.session.remove()
        ticket = db.session.get(Ticket, ticket_id)
        return [(h.field, h.new_value, h.actor.username if h.actor else None)
                for h in reversed(ticket.history)]


def test_full_support_journey(client, app):
    ids = seed(app)

    # A regular user reports a problem.
    log_in_as(client, "user1@demo.test")
    ticket_id = create_ticket(client, "Printer jammed")
    assert b"Printer jammed" in client.get("/dashboard").data

    # Another user cannot see it.
    log_in_as(client, "user2@demo.test")
    assert client.get(f"/tickets/{ticket_id}").status_code == 404
    assert b"Printer jammed" not in client.get("/tickets").data

    # The support agent takes it, works on it and replies.
    log_in_as(client, "support@demo.test")
    assert b"Printer jammed" in client.get("/tickets").data
    post_form(client, f"/tickets/{ticket_id}/assign", {"assigned_to_id": str(ids["support"])})
    post_form(client, f"/tickets/{ticket_id}/status", {"status": "In Progress"})
    post_form(client, f"/tickets/{ticket_id}/comments", {"body": "Replacing the roller now."})

    # The user sees the reply and answers.
    log_in_as(client, "user1@demo.test")
    page = client.get(f"/tickets/{ticket_id}").data
    assert b"Replacing the roller now." in page and b"In Progress" in page
    post_form(client, f"/tickets/{ticket_id}/comments", {"body": "Thank you!"})

    # The agent resolves it.
    log_in_as(client, "support@demo.test")
    post_form(client, f"/tickets/{ticket_id}/status", {"status": "Resolved"})

    assert history(app, ticket_id) == [
        ("created", "Printer jammed", "user1"),
        ("assigned_to", "support", "support"),
        ("status", "In Progress", "support"),
        ("status", "Resolved", "support"),
    ]
    with app.app_context():
        ticket = db.session.get(Ticket, ticket_id)
        assert ticket.status == "Resolved"
        assert [c.author.username for c in ticket.comments] == ["support", "user1"]

    # The user's dashboard counts the resolved ticket.
    log_in_as(client, "user1@demo.test")
    page = client.get("/dashboard").data.decode()
    assert "Total tickets" in page and "Printer jammed" in page


def test_admin_promotes_user_who_then_works_tickets(client, app):
    ids = seed(app)
    log_in_as(client, "user1@demo.test")
    ticket_id = create_ticket(client, "VPN not connecting")

    log_in_as(client, "admin@demo.test")
    post_form(client, f"/admin/users/{ids['user2']}/role", {"role": "support"})

    log_in_as(client, "user2@demo.test")
    assert client.get(f"/tickets/{ticket_id}").status_code == 200
    post_form(client, f"/tickets/{ticket_id}/status", {"status": "In Progress"})
    with app.app_context():
        assert db.session.get(Ticket, ticket_id).status == "In Progress"


def test_regular_user_cannot_reach_staff_actions(client, app):
    ids = seed(app)
    log_in_as(client, "user1@demo.test")
    ticket_id = create_ticket(client, "Email bounce")
    assert client.get("/admin/users").status_code == 403
    assert post_form(client, f"/tickets/{ticket_id}/status", {"status": "In Progress"}).status_code == 403
    assert post_form(client, f"/tickets/{ticket_id}/assign",
                     {"assigned_to_id": str(ids["support"])}).status_code == 403
    with app.app_context():
        ticket = db.session.get(Ticket, ticket_id)
        assert ticket.status == "Open" and ticket.assigned_to_id is None


def test_every_main_page_loads_for_each_role(client, app):
    seed(app)
    log_in_as(client, "user1@demo.test")
    ticket_id = create_ticket(client, "Monitor flickers")
    pages = ["/", "/dashboard", "/tickets", "/tickets/new", f"/tickets/{ticket_id}",
             f"/tickets/{ticket_id}/edit"]
    for email in ("user1@demo.test", "support@demo.test", "admin@demo.test"):
        log_in_as(client, email)
        for url in pages:
            assert client.get(url).status_code == 200, (email, url)
    assert client.get("/admin/users").status_code == 200   # still logged in as admin
    