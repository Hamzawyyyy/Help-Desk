import pytest
from app import create_app, db


@pytest.fixture
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-only-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"),
    })
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def post_form(client, url, data=None):
    client.get("/auth/login")
    with client.session_transaction() as session:
        token = session["csrf_token"]
    return client.post(url, data={**(data or {}), "csrf_token": token})
