"""Shared test fixtures (Member 5). Every test gets a fresh, empty in-memory database."""
import pytest

from app import create_app, db

PASSWORD = "Password123"


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def users(app):
    """Creates admin, user1, user2. Returns {username: id}."""
    from app.models import User

    with app.app_context():
        for name, role in [("admin", "admin"), ("user1", "user"), ("user2", "user")]:
            user = User(username=name, email=f"{name}@test.com", role=role)
            user.set_password(PASSWORD)
            db.session.add(user)
        db.session.commit()
        return {u.username: u.id for u in User.query.all()}


@pytest.fixture
def login(client):
    def _login(username, password=PASSWORD):
        return client.post("/login", data={"username": username, "password": password})
    return _login


@pytest.fixture
def make_ticket(app, users):
    """make_ticket("user1") creates a ticket owned by user1 and returns its id."""
    from app.models import Ticket

    def _make(owner="user1", title="Printer is broken", status="Open"):
        with app.app_context():
            ticket = Ticket(title=title, description="It does not print anything.",
                            category="Technical", priority="Medium", status=status,
                            created_by_id=users[owner])
            db.session.add(ticket)
            db.session.commit()
            return ticket.id
    return _make