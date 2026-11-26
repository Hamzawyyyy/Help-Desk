"""Member 4 — database tables for the change history."""
from app import db
from app.models import utc_now


class TicketHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    field = db.Column(db.String(30), nullable=False)   # created, status, assigned_to, title, ...
    old_value = db.Column(db.String(200), nullable=False, default="")
    new_value = db.Column(db.String(200), nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    ticket = db.relationship("Ticket", backref=db.backref(
        "history", order_by="TicketHistory.id.desc()", cascade="all, delete-orphan"))
    actor = db.relationship("User")