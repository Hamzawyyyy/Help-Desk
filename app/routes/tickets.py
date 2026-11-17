from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from app import db
from app.models import Ticket, User, CATEGORIES, PRIORITIES

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
        values, errors = validate_ticket_form()
        if not errors:
            ticket = Ticket(**values, creator_id=current_user.id, status="Open")
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
    ticket = visible_ticket(ticket_id)
    return render_ticket_detail(ticket)


def validate_ticket_form():
    values = {name: request.form.get(name, "").strip()
              for name in ("title", "description", "category", "priority")}
    errors = []
    if not 1 <= len(values["title"]) <= 200:
        errors.append("Title is required and must be at most 200 characters.")
    if not 1 <= len(values["description"]) <= 10000:
        errors.append("Description is required and must be at most 10,000 characters.")
    if values["category"] not in CATEGORIES:
        errors.append("Choose a valid category.")
    if values["priority"] not in PRIORITIES:
        errors.append("Choose a valid priority.")
    return values, errors


def visible_ticket(ticket_id):
    if ticket_id > 9223372036854775807:
        abort(404)
    query = db.select(Ticket).where(Ticket.id == ticket_id)
    if current_user.role == "user":
        query = query.where(Ticket.creator_id == current_user.id)
    # Private and nonexistent tickets have the same response.
    return db.first_or_404(query)


def render_ticket_detail(ticket, assignment_error=None):
    agents = []
    if current_user.role in ("support", "admin"):
        agents = db.session.scalars(
            db.select(User).where(User.role == "support").order_by(User.username)
        ).all()
    return render_template("tickets/detail.html", ticket=ticket, agents=agents,
                           assignment_error=assignment_error), 400 if assignment_error else 200


@tickets.route("/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    require_ticket_role()
    ticket = visible_ticket(ticket_id)
    errors = []
    values = {name: getattr(ticket, name)
              for name in ("title", "description", "category", "priority")}
    if request.method == "POST":
        values, errors = validate_ticket_form()
        if not errors:
            # Explicit allowlist: creator, status and assignment are not editable here.
            for name, value in values.items():
                setattr(ticket, name, value)
            db.session.commit()
            flash("Ticket updated successfully.", "success")
            return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))
    return render_template("tickets/edit.html", ticket=ticket, values=values,
                           categories=CATEGORIES, priorities=PRIORITIES,
                           errors=errors), 400 if errors else 200


@tickets.post("/<int:ticket_id>/assign")
@login_required
def assign_ticket(ticket_id):
    require_ticket_role()
    if current_user.role not in ("support", "admin"):
        abort(403)
    ticket = visible_ticket(ticket_id)
    selected = request.form.get("assigned_to_id")
    agent_id = None
    if selected != "":
        try:
            agent_id = int(selected)
        except (TypeError, ValueError):
            return render_ticket_detail(ticket, "Choose a valid support agent or Unassigned.")
        agent = db.session.get(User, agent_id) if 0 < agent_id <= 9223372036854775807 else None
        if agent is None or agent.role != "support":
            return render_ticket_detail(ticket, "Choose a valid support agent or Unassigned.")
    ticket.assigned_to_id = agent_id
    db.session.commit()
    flash("Ticket assignment updated.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))
