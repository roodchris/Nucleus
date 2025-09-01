from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, UserRole
from .forms import SignupForm, LoginForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("opportunities.home"))
    form = SignupForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("auth.login"))
        user = User(
            email=form.email.data.lower(),
            name=form.name.data,
            role=UserRole(form.role.data),
            organization=form.organization.data if form.role.data == UserRole.EMPLOYER.value else None,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome! Account created.", "success")
        return redirect(url_for("opportunities.home"))
    return render_template("auth/signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("opportunities.home"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
        else:
            login_user(user, remember=form.remember.data)
            flash("Logged in successfully.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("opportunities.home"))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
