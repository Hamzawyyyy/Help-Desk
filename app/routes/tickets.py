from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app import db
from app.models import Ticket, CATEGORIES, PRIORITIES

tickets = Blueprint("tickets", __name__, url_prefix="/tickets")


def require_ticket_role():
    if current_user.role not in ("user", "support", "admin"):
        abort(403)


@tickets.get("")
@login_required
def list_tickets():
    require_ticket_role()
    query = db.select(Ticket)
    if current_user.role == "user":
        query = query.where(Ticket.creator_id == current_user.id)
    page = db.paginate(query.order_by(Ticket.created_at.desc(), Ticket.id.desc()), per_page=20)
    return render_template("tickets/list.html", page=page)


@tickets.route("/new", methods=["GET", "POST"])
@login_required
def create_ticket():
    require_ticket_role()
    errors = []
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        priority = request.form.get("priority", "")
        if not 1 <= len(title) <= 200:
            errors.append("Title is required and must be at most 200 characters.")
        if not 1 <= len(description) <= 10000:
            errors.append("Description is required and must be at most 10,000 characters.")
        if category not in CATEGORIES:
            errors.append("Choose a valid category.")
        if priority not in PRIORITIES:
            errors.append("Choose a valid priority.")
        if not errors:
            ticket = Ticket(title=title, description=description, category=category,
                            priority=priority, creator_id=current_user.id, status="Open")
            db.session.add(ticket)
            db.session.commit()
            flash("Ticket created successfully.", "success")
            return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))
    return render_template("tickets/create.html", categories=CATEGORIES,
                           priorities=PRIORITIES, errors=errors), 400 if errors else 200


@tickets.get("/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    require_ticket_role()
    query = db.select(Ticket).where(Ticket.id == ticket_id)
    if current_user.role == "user":
        query = query.where(Ticket.creator_id == current_user.id)
    # A private ticket and a nonexistent ticket both return 404.
    ticket = db.first_or_404(query)
    return render_template("tickets/detail.html", ticket=ticket)
