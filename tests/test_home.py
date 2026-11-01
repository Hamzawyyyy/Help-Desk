from app import create_app


def test_homepage():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'HelpDesk' in response.data
