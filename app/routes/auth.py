import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not re.fullmatch(r"[A-Za-z0-9_]{3,80}", username):
            flash("Username must be 3-80 letters, numbers or underscores.", "danger")
        elif len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            flash("Enter a valid email address.", "danger")
        elif not 8 <= len(password) <= 128:
            flash("Password must contain 8-128 characters.", "danger")
        else:
            user = User(username=username, email=email, role="user")
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Username or email is already registered.", "danger")
            else:
                flash("Account created. Please log in.", "success")
                return redirect(url_for("auth.login"))
        return render_template("auth/register.html"), 400
    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(db.select(User).where(User.email == email))
        if len(password) <= 128 and user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))
        flash("Invalid email or password.", "danger")
        return render_template("auth/login.html"), 400
    return render_template("auth/login.html")


@auth.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))
