"""Exercise the integrated demo over real HTTP with disposable SQLite data."""
import re
from http.cookiejar import CookieJar
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import build_opener, HTTPCookieProcessor
from werkzeug.serving import make_server
from app import db
from app.models import User, Ticket


class Browser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(self, path, data=None):
        encoded = urlencode(data).encode() if data is not None else None
        try:
            response = self.opener.open(self.base_url + path, data=encoded, timeout=10)
        except HTTPError as response:
            return response.code, response.read().decode(), urlparse(response.url).path
        with response:
            return response.status, response.read().decode(), urlparse(response.url).path

    def post(self, path, data=None):
        status, html, _ = self.request("/auth/login")
        assert status == 200
        token = re.search(r'name="csrf_token" value="([a-f0-9]+)"', html).group(1)
        return self.request(path, {**(data or {}), "csrf_token": token})

    def register_and_login(self, username):
        values = {"username": username, "email": f"{username}@example.test",
                  "password": "disposable-test-password"}
        assert self.post("/auth/register", values)[0] == 200
        assert self.post("/auth/login", values)[2] == "/"


def test_integrated_demo_over_http(app):
    server = make_server("127.0.0.1", 0, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        owner, other, agent = (Browser(base_url) for _ in range(3))
        owner.register_and_login("demo_owner")
        status, html, detail_path = owner.post("/tickets/new", {
            "title": "HTTP demo ticket", "description": "Initial description",
            "category": "Technical", "priority": "Low"})
        assert status == 200 and detail_path.startswith("/tickets/")
        assert "Ticket created successfully" in html
        ticket_id = int(detail_path.rsplit("/", 1)[1])
        status, html, _ = owner.post(detail_path + "/edit", {
            "title": "Edited HTTP ticket", "description": "Saved owner edit",
            "category": "General", "priority": "High"})
        assert status == 200 and "Ticket updated successfully" in html

        other.register_and_login("demo_other")
        assert "Edited HTTP ticket" not in other.request("/tickets")[1]
        assert other.request(detail_path)[0] == 404
        assert other.request(detail_path + "/edit")[0] == 404
        assert other.post(detail_path + "/edit", {"title": "Unauthorized"})[0] == 404
        assert other.post(detail_path + "/assign", {"assigned_to_id": ""})[0] == 403

        agent.register_and_login("demo_agent")
        # Mirrors the README's deliberate local developer setup, in the test DB only.
        with app.app_context():
            support = db.session.scalar(db.select(User).where(User.username == "demo_agent"))
            support.role = "support"
            support_id = support.id
            db.session.commit()
        assert "Edited HTTP ticket" in agent.request("/tickets")[1]
        status, html, _ = agent.post(detail_path + "/assign", {"assigned_to_id": support_id})
        assert status == 200 and "Ticket assignment updated" in html
        assert "demo_agent</dd>" in owner.request(detail_path)[1]
        assert "Save assignment" not in owner.request(detail_path)[1]
        assert agent.post(detail_path + "/assign", {"assigned_to_id": ""})[0] == 200
        assert agent.post(detail_path + "/assign", {"assigned_to_id": support_id})[0] == 200
        assert owner.request(detail_path + "/edit", {"csrf_token": "bad-\u00e9"})[0] == 400
        assert other.post("/auth/logout")[2] == "/"
        assert other.request(detail_path + "/edit")[2] == "/auth/login"

        with app.app_context():
            db.session.remove()
            ticket = db.session.get(Ticket, ticket_id)
            assert ticket.title == "Edited HTTP ticket" and ticket.description == "Saved owner edit"
            assert ticket.status == "Open" and ticket.priority == "High"
            assert ticket.creator.username == "demo_owner"
            assert ticket.assigned_to_id == support_id
            assert db.session.scalar(db.select(db.func.count(Ticket.id))) == 1
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
