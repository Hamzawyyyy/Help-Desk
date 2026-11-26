"""Member 4 — tests for status changes and the change history."""
import pytest
from app import db
from app.models import Ticket, User
from app.member4_workflow import rules
from app.member4_workflow.models import TicketHistory
from conftest import post_form
from test_tickets import users, login, create  # noqa: F401  (shared fixtures from Member 3's tests)


def new_ticket(app, users, owner="owner", status="Open"):
    with app.app_context():
        ticket = Ticket(title="Laptop broken", description="Screen stays black.",
                        category="Technical", priority="High", creator_id=users[owner],
                        status=status)
        db.session.add(ticket)
        db.session.commit()
        return ticket.id


def ticket_state(app, ticket_id):
    with app.app_context():
        db.session.remove()
        ticket = db.session.get(Ticket, ticket_id)
        return {
            "status": ticket.status,
            "history": [(h.field, h.old_value, h.new_value, h.actor.username if h.actor else None)
                        for h in ticket.history],
        }


def set_status(client, ticket_id, status):
    return post_form(client, f"/tickets/{ticket_id}/status", {"status": status})


# ---------- status rules ----------

@pytest.mark.parametrize("actor", ["agent", "admin"])
def test_staff_moves_open_to_in_progress(client, app, users, actor):
    ticket_id = new_ticket(app, users)
    login(client, actor)
    response = set_status(client, ticket_id, "In Progress")
    assert response.status_code == 302
    assert ticket_state(app, ticket_id)["status"] == "In Progress"
    assert b"Status changed to In Progress" in client.get(response.location).data


def test_full_lifecycle_with_reopen(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "agent")
    for status in ("In Progress", "Resolved", "Open"):
        set_status(client, ticket_id, status)
        assert ticket_state(app, ticket_id)["status"] == status


def test_in_progress_can_go_back_to_open(client, app, users):
    ticket_id = new_ticket(app, users, status="In Progress")
    login(client, "agent")
    set_status(client, ticket_id, "Open")
    assert ticket_state(app, ticket_id)["status"] == "Open"


@pytest.mark.parametrize("start, target", [
    ("Open", "Resolved"), ("Open", "Open"), ("Resolved", "In Progress"),
    ("Open", "Closed"), ("Open", ""),
])
def test_invalid_transitions_are_rejected(client, app, users, start, target):
    ticket_id = new_ticket(app, users, status=start)
    login(client, "agent")
    response = set_status(client, ticket_id, target)
    state = ticket_state(app, ticket_id)
    assert state["status"] == start
    assert all(field != "status" for field, *_ in state["history"])
    assert b"cannot go from" in client.get(response.location).data


def test_ticket_owner_cannot_change_status(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    assert set_status(client, ticket_id, "In Progress").status_code == 403
    assert ticket_state(app, ticket_id)["status"] == "Open"


def test_other_user_gets_404_for_status_change(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "other")
    assert set_status(client, ticket_id, "In Progress").status_code == 404


def test_status_change_needs_csrf_token(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "agent")
    assert client.post(f"/tickets/{ticket_id}/status", data={"status": "In Progress"}).status_code == 400
    assert ticket_state(app, ticket_id)["status"] == "Open"


def test_rules_table():
    assert rules.allowed_next_statuses(Ticket(status="Open")) == ["In Progress"]
    assert rules.allowed_next_statuses(Ticket(status="In Progress")) == ["Resolved", "Open"]
    assert rules.allowed_next_statuses(Ticket(status="Resolved")) == ["Open"]


def test_service_refuses_regular_user(app, users):
    ticket_id = new_ticket(app, users)
    with app.app_context():
        ticket = db.session.get(Ticket, ticket_id)
        owner = db.session.get(User, users["owner"])
        with pytest.raises(PermissionError):
            rules.change_status(ticket, "In Progress", owner)


# ---------- history ----------

def test_creating_through_the_website_logs_history(client, app, users):
    login(client, "owner")
    response = create(client)
    ticket_id = int(response.location.rstrip("/").split("/")[-1])
    assert ticket_state(app, ticket_id)["history"] == [("created", "", "Printer offline", "owner")]


def test_status_change_logs_old_new_and_actor(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "agent")
    set_status(client, ticket_id, "In Progress")
    assert ticket_state(app, ticket_id)["history"][0] == ("status", "Open", "In Progress", "agent")


def test_assignment_and_edit_are_logged(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "admin")
    post_form(client, f"/tickets/{ticket_id}/assign", {"assigned_to_id": str(users["agent"])})
    post_form(client, f"/tickets/{ticket_id}/edit", {"title": "Laptop broken", "description": "Screen stays black.",
                                                      "category": "Technical", "priority": "Low"})
    history = ticket_state(app, ticket_id)["history"]
    assert ("priority", "High", "Low", "admin") in history
    assert ("assigned_to", "", "agent", "admin") in history


def test_history_is_newest_first(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "agent")
    set_status(client, ticket_id, "In Progress")
    set_status(client, ticket_id, "Resolved")
    statuses = [new for field, old, new, actor in ticket_state(app, ticket_id)["history"] if field == "status"]
    assert statuses == ["Resolved", "In Progress"]


def test_unchanged_edit_logs_nothing(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    before = len(ticket_state(app, ticket_id)["history"])
    post_form(client, f"/tickets/{ticket_id}/edit", {"title": "Laptop broken", "description": "Screen stays black.",
                                                      "category": "Technical", "priority": "High"})
    assert len(ticket_state(app, ticket_id)["history"]) == before


def test_detail_page_shows_status_buttons_only_to_staff(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "agent")
    page = client.get(f"/tickets/{ticket_id}").data
    assert b"Change status" in page and b"History" in page
    post_form(client, "/auth/logout")
    login(client, "owner")
    page = client.get(f"/tickets/{ticket_id}").data
    assert b"Change status" not in page and b"History" in page


def test_deleting_a_ticket_removes_its_history(app, users):
    ticket_id = new_ticket(app, users)
    with app.app_context():
        db.session.delete(db.session.get(Ticket, ticket_id))
        db.session.commit()
        assert db.session.query(TicketHistory).count() == 0