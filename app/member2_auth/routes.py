"""Member 2 — admin page for managing user roles."""
from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app import db
from app.models import User
from . import bp
from .permissions import ROLES, admin_required


@bp.get("/admin/users")
@admin_required
def list_users():
    all_users = db.session.scalars(db.select(User).order_by(User.username)).all()
    return render_template("users/list.html", users=all_users, roles=ROLES)


@bp.post("/admin/users/<int:user_id>/role")
@admin_required
def change_role(user_id):
    if user_id > 9223372036854775807:
        abort(404)
    user = db.get_or_404(User, user_id)
    new_role = request.form.get("role", "")
    if new_role not in ROLES:
        flash("Choose a valid role.", "danger")
    elif user.id == current_user.id:
        flash("You cannot change your own role.", "warning")
    elif user.role == new_role:
        flash(f"{user.username} already has the {new_role} role.", "info")
    else:
        user.role = new_role
        db.session.commit()
        flash(f"{user.username} is now {new_role}.", "success")
    return redirect(url_for("member2_auth.list_users"))