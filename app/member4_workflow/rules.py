"""Member 4 — the business rules.

    From          Allowed next               Who
    Open          In Progress                support / admin
    In Progress   Resolved, or back to Open  support / admin
    Resolved      Open (reopen)              support / admin

Every change to a ticket (creation, edits, assignment, status) is written to
TicketHistory automatically by the listener at the bottom of this file, so the
ticket pages written by Member 3 do not need to call anything.
"""
from flask import has_request_context
from flask_login import current_user
from sqlalchemy import event, inspect
from app import db
from app.models import Ticket, User
from .models import TicketHistory

STATUSES = ("Open", "In Progress", "Resolved")
TRANSITIONS = {
    "Open": ("In Progress",),
    "In Progress": ("Resolved", "Open"),
    "Resolved": ("Open",),   # reopen — delete this line if the team does not want reopening
}
STAFF_ROLES = ("support", "admin")
TRACKED_FIELDS = ("title", "description", "category", "priority", "status", "assigned_to_id")


class WorkflowError(ValueError):
    """A request that breaks a business rule; shown to the user as a message."""


def allowed_next_statuses(ticket):
    return list(TRANSITIONS.get(ticket.status, ()))


def change_status(ticket, new_status, actor):
    if actor.role not in STAFF_ROLES:
        raise PermissionError("Only support agents and admins can change the status.")
    if new_status not in allowed_next_statuses(ticket):
        raise WorkflowError(f"A ticket cannot go from {ticket.status} to {new_status or 'nothing'}.")
    ticket.status = new_status
    db.session.commit()   # the listener below records the history line


def describe(entry):
    """One readable sentence for the history list."""
    who = entry.actor.username if entry.actor else "System"
    if entry.field == "created":
        return f"{who} created the ticket"
    if entry.field == "assigned_to":
        return f"{who} assigned the ticket to {entry.new_value or 'nobody'}"
    if entry.field == "description":
        return f"{who} edited the description"
    return f"{who} changed {entry.field} from “{entry.old_value}” to “{entry.new_value}”"


# ---- automatic history log -------------------------------------------------

def _actor_id():
    if has_request_context() and current_user.is_authenticated:
        return current_user.id
    return None


def _display(session, field, value):
    if value is None:
        return ""
    if field == "assigned_to_id":
        user = session.get(User, value)
        return user.username if user else str(value)
    return str(value)[:200]


@event.listens_for(db.session, "before_flush")
def record_ticket_history(session, flush_context, instances):
    actor_id = _actor_id()
    with session.no_autoflush:
        for obj in list(session.new):
            if isinstance(obj, Ticket):
                session.add(TicketHistory(ticket=obj, actor_id=actor_id, field="created",
                                          new_value=(obj.title or "")[:200]))
        for obj in list(session.dirty):
            if not isinstance(obj, Ticket) or not session.is_modified(obj):
                continue
            state = inspect(obj)
            for field in TRACKED_FIELDS:
                change = state.attrs[field].history
                if not change.has_changes():
                    continue
                old = change.deleted[0] if change.deleted else None
                new = change.added[0] if change.added else None
                if old == new:
                    continue
                name = "assigned_to" if field == "assigned_to_id" else field
                session.add(TicketHistory(ticket=obj, actor_id=actor_id, field=name,
                                          old_value=_display(session, field, old),
                                          new_value=_display(session, field, new)))