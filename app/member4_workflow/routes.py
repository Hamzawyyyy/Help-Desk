"""Member 4 — the status-change action and helpers for the ticket panel."""
from flask import redirect, request, url_for, flash, abort
from flask_login import current_user, login_required
from app.routes.tickets import require_ticket_role, visible_ticket
from . import bp
from . import rules


@bp.app_context_processor
def workflow_helpers():
    """Lets the ticket panel template use these rules."""
    return {"allowed_next_statuses": rules.allowed_next_statuses,
            "describe_history": rules.describe}


@bp.post("/tickets/<int:ticket_id>/status")
@login_required
def change_status(ticket_id):
    require_ticket_role()
    ticket = visible_ticket(ticket_id)
    try:
        rules.change_status(ticket, request.form.get("status", ""), current_user)
    except PermissionError:
        abort(403)
    except rules.WorkflowError as error:
        flash(str(error), "danger")
    else:
        flash(f"Status changed to {ticket.status}.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))