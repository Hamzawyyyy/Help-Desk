"""Member 4 — tests for comments on tickets."""
import pytest
from app import db
from app.models import Ticket
from app.member4_workflow.models import Comment
from conftest import post_form
from test_tickets import users, login  # noqa: F401  (shared fixtures from Member 3's tests)


def new_ticket(app, users, owner="owner"):
    with app.app_context():
        ticket = Ticket(title="Laptop broken", description="Screen stays black.",
                        category="Technical", priority="High", creator_id=users[owner])
        db.session.add(ticket)
        db.session.commit()
        return ticket.id


def comments_of(app, ticket_id):
    with app.app_context():
        db.session.remove()
        return [(c.author.username, c.body) for c in db.session.get(Ticket, ticket_id).comments]


def comment(client, ticket_id, body):
    return post_form(client, f"/tickets/{ticket_id}/comments", {"body": body})


def test_owner_comments_on_own_ticket(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    response = comment(client, ticket_id, "  Any update?  ")
    assert comments_of(app, ticket_id) == [("owner", "Any update?")]
    assert b"Comment added" in client.get(response.location).data


@pytest.mark.parametrize("actor", ["agent", "admin"])
def test_staff_comment_on_any_ticket(client, app, users, actor):
    ticket_id = new_ticket(app, users)
    login(client, actor)
    comment(client, ticket_id, "Looking into it.")
    assert comments_of(app, ticket_id) == [(actor, "Looking into it.")]


def test_other_user_cannot_comment(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "other")
    assert comment(client, ticket_id, "Hello").status_code == 404
    assert comments_of(app, ticket_id) == []


def test_logged_out_visitor_cannot_comment(client, app, users):
    ticket_id = new_ticket(app, users)
    response = comment(client, ticket_id, "Hello")
    assert response.status_code == 302 and "/auth/login" in response.location
    assert comments_of(app, ticket_id) == []


@pytest.mark.parametrize("body", ["", "   ", "\n\t", "x" * 2001])
def test_invalid_comments_are_rejected(client, app, users, body):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    response = comment(client, ticket_id, body)
    assert comments_of(app, ticket_id) == []
    page = client.get(response.location).data
    assert b"cannot be empty" in page or b"at most 2000" in page


def test_comment_needs_csrf_token(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    assert client.post(f"/tickets/{ticket_id}/comments", data={"body": "Hi"}).status_code == 400
    assert comments_of(app, ticket_id) == []


def test_comments_are_oldest_first_and_escaped(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    comment(client, ticket_id, "first")
    comment(client, ticket_id, "<script>alert(1)</script>")
    assert [body for _, body in comments_of(app, ticket_id)] == ["first", "<script>alert(1)</script>"]
    page = client.get(f"/tickets/{ticket_id}").data
    assert b"&lt;script&gt;" in page and b"<script>alert(1)</script>" not in page


def test_ticket_page_shows_comment_form(client, app, users):
    ticket_id = new_ticket(app, users)
    login(client, "owner")
    page = client.get(f"/tickets/{ticket_id}").data
    assert b"Comments (0)" in page and b"Add a comment" in page


def test_deleting_a_ticket_removes_its_comments(app, users):
    ticket_id = new_ticket(app, users)
    with app.app_context():
        db.session.add(Comment(ticket_id=ticket_id, author_id=users["owner"], body="hi"))
        db.session.commit()
        db.session.delete(db.session.get(Ticket, ticket_id))
        db.session.commit()
        assert db.session.query(Comment).count() == 0