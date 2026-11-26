"""Member 1 — tests for the dashboard page."""
import pytest
from app import db
from app.models import Ticket, User
from app.member1_frontend.routes import build_stats
from test_tickets import users, login  # noqa: F401  (shared fixtures from Member 3's tests)


def add_ticket(app, users, owner, status="Open", priority="Medium", assigned=None, title="Sample"):
    with app.app_context():
        ticket = Ticket(title=title, description="Details", category="General", priority=priority,
                        status=status, creator_id=users[owner],
                        assigned_to_id=users[assigned] if assigned else None)
        db.session.add(ticket)
        db.session.commit()


def stats_for(app, users, username):
    with app.app_context():
        return build_stats(db.session.get(User, users[username]))


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302 and "/auth/login" in response.location


def test_user_sees_only_own_counts(app, users):
    add_ticket(app, users, "owner", status="Open")
    add_ticket(app, users, "owner", status="Resolved", priority="High")
    add_ticket(app, users, "other", status="Open")
    stats = stats_for(app, users, "owner")
    assert stats["total"] == 2
    assert stats["by_status"] == {"Open": 1, "In Progress": 0, "Resolved": 1}
    assert stats["by_priority"]["High"] == 1
    assert "assigned_to_me" not in stats


@pytest.mark.parametrize("actor", ["agent", "admin"])
def test_staff_see_all_counts(app, users, actor):
    add_ticket(app, users, "owner", assigned="agent")
    add_ticket(app, users, "other")
    add_ticket(app, users, "other", status="Resolved")
    stats = stats_for(app, users, actor)
    assert stats["total"] == 3
    assert stats["unassigned"] == 1
    assert stats["assigned_to_me"] == (1 if actor == "agent" else 0)


def test_dashboard_page_shows_latest_tickets(client, app, users):
    add_ticket(app, users, "owner", title="Printer jammed")
    login(client, "owner")
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert b"Total tickets" in page.data and b"Printer jammed" in page.data


def test_dashboard_hides_other_users_tickets(client, app, users):
    add_ticket(app, users, "other", title="Private ticket")
    login(client, "owner")
    page = client.get("/dashboard")
    assert b"Private ticket" not in page.data and b"No tickets yet" in page.data


def test_dashboard_escapes_titles(client, app, users):
    add_ticket(app, users, "owner", title="<script>alert(1)</script>")
    login(client, "owner")
    page = client.get("/dashboard").data
    assert b"&lt;script&gt;" in page and b"<script>alert(1)</script>" not in page


def test_unknown_role_gets_403(client, users):
    login(client, "unknown")
    assert client.get("/dashboard").status_code == 403


def test_menu_and_home_link_to_dashboard(client, users):
    login(client, "owner")
    page = client.get("/").data
    assert b'href="/dashboard"' in page and b"Go to dashboard" in page