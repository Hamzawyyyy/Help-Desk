"""Member 1 — the dashboard page."""
from collections import Counter
from flask import render_template
from flask_login import current_user, login_required
from app import db
from app.models import Ticket, PRIORITIES
from . import bp

STATUSES = ("Open", "In Progress", "Resolved")
STAFF_ROLES = ("support", "admin")


def build_stats(user):
    """Counts for the tickets this user is allowed to see (same rule as the ticket list)."""
    query = db.select(Ticket).order_by(Ticket.created_at.desc(), Ticket.id.desc())
    if user.role not in STAFF_ROLES:
        query = query.where(Ticket.creator_id == user.id)
    tickets = db.session.scalars(query).all()
    by_status = Counter(t.status for t in tickets)
    by_priority = Counter(t.priority for t in tickets)
    stats = {
        "total": len(tickets),
        "by_status": {status: by_status.get(status, 0) for status in STATUSES},
        "by_priority": {priority: by_priority.get(priority, 0) for priority in PRIORITIES},
        "recent": tickets[:5],
    }
    if user.role in STAFF_ROLES:
        open_tickets = [t for t in tickets if t.status != "Resolved"]
        stats["assigned_to_me"] = sum(1 for t in open_tickets if t.assigned_to_id == user.id)
        stats["unassigned"] = sum(1 for t in open_tickets if t.assigned_to_id is None)
    return stats


@bp.get("/dashboard")
@login_required
def dashboard():
    if current_user.role not in ("user", "support", "admin"):
        return render_template("dashboard/index.html", stats=None), 403
    return render_template("dashboard/index.html", stats=build_stats(current_user))