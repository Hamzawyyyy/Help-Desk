"""Shared database models."""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


CATEGORIES = ("General", "Technical", "Account", "Billing")
PRIORITIES = ("Low", "Medium", "High")


def utc_now():
    # SQLite stores these as naive datetimes; all application timestamps are UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), nullable=False)
    priority = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Open")
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    creator = db.relationship("User", foreign_keys=[creator_id], backref="created_tickets")
    assigned_to = db.relationship("User", foreign_keys=[assigned_to_id], backref="assigned_tickets")
    __table_args__ = (
        db.CheckConstraint("category IN ('General', 'Technical', 'Account', 'Billing')", name="ticket_category"),
        db.CheckConstraint("priority IN ('Low', 'Medium', 'High')", name="ticket_priority"),
        db.CheckConstraint("length(trim(title)) BETWEEN 1 AND 200", name="ticket_title_length"),
        db.CheckConstraint("length(trim(description)) BETWEEN 1 AND 10000", name="ticket_description_length"),
    )
