import pytest
from datetime import datetime, timezone
from app import db
from app.models import User, Ticket
from conftest import post_form


@pytest.fixture
def users(app):
    with app.app_context():
        ids = {}
        for username, role in (("owner", "user"), ("other", "user"),
                               ("agent", "support"), ("admin", "admin"), ("unknown", "unknown")):
            user = User(username=username, email=f"{username}@example.test", role=role)
            user.set_password("test-password")
            db.session.add(user)
            db.session.flush()
            ids[username] = user.id
        db.session.commit()
        return ids


def login(client, username):
    response = post_form(client, "/auth/login", {
        "email": f"{username}@example.test", "password": "test-password"})
    assert response.status_code == 302


def create(client, **changes):
    data = {"title": "Printer offline", "description": "Cannot print in lab.",
            "category": "Technical", "priority": "Medium"}
    return post_form(client, "/tickets/new", {**data, **changes})


def test_create_persist_and_view(client, app, users):
    login(client, "owner")
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    response = create(client, creator_id=users["other"], status="Closed", assigned_to_id=users["agent"])
    assert response.status_code == 302
    with app.app_context():
        db.session.remove()
        ticket = db.session.scalar(db.select(Ticket))
        assert ticket.title == "Printer offline"
        assert ticket.description == "Cannot print in lab."
        assert ticket.creator_id == users["owner"]
        assert ticket.category == "Technical" and ticket.priority == "Medium"
        assert ticket.status == "Open" and ticket.assigned_to_id is None
        assert ticket.created_at >= before and ticket.updated_at >= before
        ticket_id = ticket.id
    detail = client.get(response.location)
    assert detail.status_code == 200
    assert b"Ticket created successfully" in detail.data
    for text in (b"Printer offline", b"Cannot print in lab.", b"Technical", b"Medium", b"Open", b"owner", b"UTC"):
        assert text in detail.data
    listing = client.get("/tickets")
    assert listing.status_code == 200
    assert f"/tickets/{ticket_id}".encode() in listing.data


@pytest.mark.parametrize("changes", [
    {"title": ""}, {"title": "   "}, {"title": "x" * 201},
    {"description": ""}, {"description": "  "}, {"description": "x" * 10001},
    {"category": "Invalid"}, {"category": ""}, {"priority": "Urgent"}, {"priority": ""},
])
def test_reject_invalid_ticket(client, app, users, changes):
    login(client, "owner")
    assert create(client, **changes).status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Ticket.id))) == 0


@pytest.mark.parametrize("missing", ["title", "description", "category", "priority"])
def test_missing_fields(client, app, users, missing):
    login(client, "owner")
    data = {"title": "Title", "description": "Description", "category": "General", "priority": "Low"}
    del data[missing]
    assert post_form(client, "/tickets/new", data).status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Ticket.id))) == 0


@pytest.mark.parametrize("role", ["owner", "other", "agent", "admin"])
def test_ticket_visibility(client, app, users, role):
    with app.app_context():
        ticket = Ticket(title="Private ticket", description="Private description", category="Account",
                        priority="High", creator_id=users["owner"])
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id
    login(client, role)
    listing = client.get("/tickets")
    details = client.get(f"/tickets/{ticket_id}")
    if role == "other":
        assert b"Private ticket" not in listing.data
        assert b"Private description" not in listing.data
        assert details.status_code == 404
    else:
        assert b"Private ticket" in listing.data
        assert details.status_code == 200


@pytest.mark.parametrize("path", ["/tickets", "/tickets/new", "/tickets/1"])
def test_anonymous_access(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_anonymous_create_and_missing_ticket(client, app, users):
    assert create(client).status_code == 302
    with app.app_context():
        assert db.session.scalar(db.select(db.func.count(Ticket.id))) == 0
    login(client, "owner")
    assert client.get("/tickets/99999").status_code == 404
    assert client.get("/tickets/not-a-number").status_code == 404
    assert client.get("/tickets/-1").status_code == 404
    assert b"No tickets yet" in client.get("/tickets").data
    assert client.get("/tickets/new").status_code == 200


def test_create_csrf_and_escape_html(client, app, users):
    login(client, "owner")
    assert client.post("/tickets/new", data={"title": "Blocked"}).status_code == 400
    response = create(client, title="<script>alert(1)</script>", description="<img src=x onerror=alert(1)>")
    detail = client.get(response.location)
    assert b"<script>alert(1)</script>" not in detail.data
    assert b"&lt;script&gt;" in detail.data
    assert b"&lt;img" in detail.data
    assert b"&lt;script&gt;" in client.get("/tickets").data


def test_unknown_role_denied(client, app, users):
    login(client, "unknown")
    assert client.get("/tickets").status_code == 403
    assert client.get("/tickets/new").status_code == 403
    assert create(client).status_code == 403
    assert client.get("/tickets/1").status_code == 403


def test_pagination_applies_visibility_before_page(client, app, users):
    with app.app_context():
        for index in range(22):
            db.session.add(Ticket(title=f"Own {index}", description="description", category="General",
                                  priority="Low", creator_id=users["owner"]))
        db.session.add(Ticket(title="Other private", description="hidden", category="Billing",
                              priority="High", creator_id=users["other"]))
        db.session.commit()
    login(client, "owner")
    first = client.get("/tickets")
    second = client.get("/tickets?page=2")
    assert first.data.count(b'<td><a href="/tickets/') == 20
    assert second.data.count(b'<td><a href="/tickets/') == 2
    assert b"Other private" not in first.data + second.data
    assert client.get("/tickets?page=999").status_code == 404


def test_validation_preserves_form_values(client, users):
    login(client, "owner")
    response = create(client, title="Keep this title", description="")
    assert b"Keep this title" in response.data
    assert b'value="Technical" selected' in response.data
    assert b'value="Medium" selected' in response.data


@pytest.mark.parametrize("category,priority", [
    ("General", "Low"), ("Technical", "Medium"), ("Account", "High"), ("Billing", "Low"),
])
def test_allowed_choices_and_length_boundaries(client, app, users, category, priority):
    login(client, "owner")
    response = create(client, title="x" * 200, description="y" * 10000,
                      category=category, priority=priority)
    assert response.status_code == 302
    with app.app_context():
        ticket = db.session.scalar(db.select(Ticket))
        assert len(ticket.title) == 200 and len(ticket.description) == 10000
        assert ticket.category == category and ticket.priority == priority
