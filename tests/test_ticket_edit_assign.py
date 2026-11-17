from datetime import datetime
import pytest
from app import db
from app.models import Ticket, User
from conftest import post_form
from test_tickets import users, login


@pytest.fixture
def existing_ticket(app, users):
    with app.app_context():
        ticket = Ticket(title="Original title", description="Original description",
                        category="General", priority="Low", creator_id=users["owner"],
                        assigned_to_id=users["agent"], status="Open",
                        created_at=datetime(2020, 1, 1), updated_at=datetime(2020, 1, 1))
        db.session.add(ticket)
        db.session.commit()
        return ticket.id


def edit(client, ticket_id, **changes):
    values = {"title": "Updated title", "description": "Updated description",
              "category": "Billing", "priority": "High"}
    return post_form(client, f"/tickets/{ticket_id}/edit", {**values, **changes})


def snapshot(app, ticket_id):
    with app.app_context():
        db.session.remove()
        ticket = db.session.get(Ticket, ticket_id)
        return {name: getattr(ticket, name) for name in (
            "title", "description", "category", "priority", "creator_id",
            "assigned_to_id", "status", "created_at", "updated_at")}


@pytest.mark.parametrize("actor", ["owner", "agent", "admin"])
def test_edit_persists_allowed_fields_only(client, app, users, existing_ticket, actor):
    login(client, actor)
    page = client.get(f"/tickets/{existing_ticket}/edit")
    assert page.status_code == 200 and b"Original title" in page.data
    before = snapshot(app, existing_ticket)
    response = edit(client, existing_ticket, creator_id=users["other"], assigned_to_id="",
                    status="Closed", created_at="2030-01-01", updated_at="2030-01-01")
    assert response.status_code == 302
    after = snapshot(app, existing_ticket)
    assert after["title"] == "Updated title" and after["description"] == "Updated description"
    assert after["category"] == "Billing" and after["priority"] == "High"
    for name in ("creator_id", "assigned_to_id", "status", "created_at"):
        assert after[name] == before[name]
    assert before["updated_at"] < after["updated_at"] < datetime(2030, 1, 1)
    assert b"Ticket updated successfully" in client.get(response.location).data


@pytest.mark.parametrize("changes", [
    {"title": ""}, {"title": "  "}, {"title": "x" * 201},
    {"description": ""}, {"description": "\n\t"}, {"description": "x" * 10001},
    {"category": "Unknown"}, {"priority": "Urgent"},
])
def test_invalid_edit_preserves_database_and_form(client, app, users, existing_ticket, changes):
    login(client, "owner")
    before = snapshot(app, existing_ticket)
    response = edit(client, existing_ticket, **changes)
    assert response.status_code == 400
    assert snapshot(app, existing_ticket) == before
    if "title" not in changes:
        assert b"Updated title" in response.data


@pytest.mark.parametrize("missing", ["title", "description", "category", "priority"])
def test_edit_missing_field_rejected(client, app, users, existing_ticket, missing):
    login(client, "owner")
    before = snapshot(app, existing_ticket)
    values = {"title": "New", "description": "New description", "category": "General", "priority": "Low"}
    del values[missing]
    assert post_form(client, f"/tickets/{existing_ticket}/edit", values).status_code == 400
    assert snapshot(app, existing_ticket) == before


@pytest.mark.parametrize("actor,expected", [("other", 404), ("unknown", 403)])
def test_unauthorized_edit(client, app, users, existing_ticket, actor, expected):
    login(client, actor)
    before = snapshot(app, existing_ticket)
    assert client.get(f"/tickets/{existing_ticket}/edit").status_code == expected
    assert edit(client, existing_ticket).status_code == expected
    assert snapshot(app, existing_ticket) == before


@pytest.mark.parametrize("actor", ["agent", "admin"])
def test_assign_and_unassign_persist(client, app, users, existing_ticket, actor):
    login(client, actor)
    before = snapshot(app, existing_ticket)
    url = f"/tickets/{existing_ticket}/assign"
    response = post_form(client, url, {"assigned_to_id": ""})
    assert response.status_code == 302
    cleared = snapshot(app, existing_ticket)
    assert cleared["assigned_to_id"] is None
    assert cleared["updated_at"] > before["updated_at"]
    assert b"Unassigned" in client.get(response.location).data
    response = post_form(client, url, {"assigned_to_id": users["agent"], "status": "Closed"})
    assert response.status_code == 302
    after = snapshot(app, existing_ticket)
    assert after["assigned_to_id"] == users["agent"]
    for name in ("title", "description", "category", "priority", "status", "creator_id", "created_at"):
        assert after[name] == before[name]
    page = client.get(response.location)
    assert b"Ticket assignment updated" in page.data
    assert f'value="{users["agent"]}" selected'.encode() in page.data
    post_form(client, "/auth/logout")
    login(client, "owner")
    owner_page = client.get(response.location)
    assert b"Assigned agent" in owner_page.data and b">agent</dd>" in owner_page.data
    assert b"Save assignment" not in owner_page.data


@pytest.mark.parametrize("selected", ["missing", "0", "-1", "9999999", "abc", "1.5", "9" * 100])
def test_invalid_agent_rejected(client, app, users, existing_ticket, selected):
    login(client, "admin")
    before = snapshot(app, existing_ticket)
    data = {} if selected == "missing" else {"assigned_to_id": selected}
    response = post_form(client, f"/tickets/{existing_ticket}/assign", data)
    assert response.status_code == 400 and b"Choose a valid support agent" in response.data
    assert snapshot(app, existing_ticket) == before


@pytest.mark.parametrize("actor", ["owner", "other", "unknown"])
def test_assignment_staff_only(client, app, users, existing_ticket, actor):
    login(client, actor)
    before = snapshot(app, existing_ticket)
    assert post_form(client, f"/tickets/{existing_ticket}/assign", {"assigned_to_id": ""}).status_code == 403
    assert snapshot(app, existing_ticket) == before


@pytest.mark.parametrize("target", ["owner", "other", "admin", "unknown"])
def test_assignment_rejects_non_support_users(client, app, users, existing_ticket, target):
    login(client, "admin")
    before = snapshot(app, existing_ticket)
    response = post_form(client, f"/tickets/{existing_ticket}/assign", {"assigned_to_id": users[target]})
    assert response.status_code == 400
    assert snapshot(app, existing_ticket) == before
    page = client.get(f"/tickets/{existing_ticket}")
    assert f'<option value="{users[target]}"'.encode() not in page.data


def test_csrf_and_anonymous_access(client, app, users, existing_ticket):
    before = snapshot(app, existing_ticket)
    assert client.get(f"/tickets/{existing_ticket}/edit").status_code == 302
    assert edit(client, existing_ticket).status_code == 302
    assert post_form(client, f"/tickets/{existing_ticket}/assign", {"assigned_to_id": ""}).status_code == 302
    login(client, "admin")
    for action in ("edit", "assign"):
        assert client.post(f"/tickets/{existing_ticket}/{action}", data={}).status_code == 400
        assert client.post(f"/tickets/{existing_ticket}/{action}", data={"csrf_token": "wrong"}).status_code == 400
    assert client.get(f"/tickets/{existing_ticket}/assign").status_code == 405
    assert snapshot(app, existing_ticket) == before


def test_missing_ticket_and_escaped_edit(client, app, users, existing_ticket):
    login(client, "admin")
    assert client.get("/tickets/99999/edit").status_code == 404
    assert edit(client, 99999).status_code == 404
    assert post_form(client, "/tickets/99999/assign", {"assigned_to_id": ""}).status_code == 404
    response = edit(client, existing_ticket, title='<script>alert(1)</script>', description='<img src=x>')
    assert response.status_code == 302
    for path in (response.location, f"/tickets/{existing_ticket}/edit"):
        page = client.get(path)
        assert b"<script>alert(1)</script>" not in page.data
        assert b"&lt;script&gt;" in page.data and b"&lt;img" in page.data


def test_oversized_ticket_ids_return_404(client, users):
    login(client, "admin")
    huge_id = "9" * 100
    assert client.get(f"/tickets/{huge_id}").status_code == 404
    assert client.get(f"/tickets/{huge_id}/edit").status_code == 404
    assert edit(client, huge_id).status_code == 404
    assert post_form(client, f"/tickets/{huge_id}/assign", {"assigned_to_id": ""}).status_code == 404


def test_reassign_and_maximum_edit_lengths(client, app, users, existing_ticket):
    with app.app_context():
        second_agent = User(username="second_agent", email="second@example.test", role="support")
        second_agent.set_password("fixture-password")
        db.session.add(second_agent)
        db.session.commit()
        second_id = second_agent.id
    login(client, "admin")
    response = post_form(client, f"/tickets/{existing_ticket}/assign", {"assigned_to_id": second_id})
    assert response.status_code == 302
    assert snapshot(app, existing_ticket)["assigned_to_id"] == second_id
    response = edit(client, existing_ticket, title=" " + "x" * 200 + " ",
                    description="y" * 10000)
    assert response.status_code == 302
    saved = snapshot(app, existing_ticket)
    assert len(saved["title"]) == 200 and len(saved["description"]) == 10000
    assert saved["assigned_to_id"] == second_id
