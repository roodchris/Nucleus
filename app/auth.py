from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, UserRole
from .forms import SignupForm, LoginForm, EmailVerificationForm
from .email_service import create_verification_record, send_verification_email, verify_email_code

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("opportunities.home"))
    
    # Check if database is working
    try:
        from flask import current_app
        if current_app.config.get('DATABASE_ERROR'):
            flash("Database connection issue. Please try again later.", "error")
            return render_template("auth/signup.html", form=SignupForm())
    except:
        pass
    
    form = SignupForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash("You already have an account. Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        
        # Check if name is already taken (optional early check)
        existing_name = User.query.filter_by(name=form.name.data).first()
        if existing_name:
            flash("This name/username is already in use. You can change it during email verification.", "warning")
        
        # Store user data in session for verification step
        session['pending_user'] = {
            'email': form.email.data.lower(),
            'name': form.name.data,
            'role': form.role.data,
            'organization': form.organization.data if form.role.data == UserRole.EMPLOYER.value else None,
            'password': form.password.data
        }
        
        # Create verification record and send email
        try:
            verification_code = create_verification_record(form.email.data.lower())
            if verification_code:
                if send_verification_email(form.email.data.lower(), verification_code):
                    flash("Verification code sent to your email. Please check your inbox.", "info")
                    return redirect(url_for("auth.verify_email"))
                else:
                    flash("Failed to send verification email. Please try again.", "error")
            else:
                flash("Failed to create verification record. Please try again.", "error")
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Signup error: {e}")
            flash("An error occurred during signup. Please try again.", "error")
    
    return render_template("auth/signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("opportunities.home"))
    
    # Check if database is working
    try:
        from flask import current_app
        if current_app.config.get('DATABASE_ERROR'):
            flash("Database connection issue. Please try again later.", "error")
            return render_template("auth/login.html", form=LoginForm())
    except:
        pass
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data.lower()).first()
            if not user or not user.check_password(form.password.data):
                flash("Invalid email or password.", "danger")
            else:
                login_user(user, remember=form.remember.data)
                flash("Logged in successfully.", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("opportunities.home"))
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Login error: {e}")
            flash("An error occurred during login. Please try again.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    if current_user.is_authenticated:
        return redirect(url_for("opportunities.home"))
    
    # Check if there's pending user data in session
    pending_user = session.get('pending_user')
    if not pending_user:
        flash("No pending verification found. Please sign up again.", "warning")
        return redirect(url_for("auth.signup"))
    
    form = EmailVerificationForm()
    if form.validate_on_submit():
        email = pending_user['email']
        code = form.verification_code.data
        
        # Get the name from the form (user can change it)
        new_name = request.form.get('name', pending_user['name']).strip()
        if not new_name:
            flash("Name/username is required.", "error")
            return render_template("auth/verify_email.html", form=form, email=pending_user['email'])
        
        success, message = verify_email_code(email, code)
        if success:
            # Check if username/name is already taken
            existing_name = User.query.filter_by(name=new_name).first()
            if existing_name:
                flash("This name/username is already in use. Please try a different name/username.", "error")
                return render_template("auth/verify_email.html", form=form, email=pending_user['email'])
            
            # Create the user account
            user = User(
                email=pending_user['email'],
                name=new_name,
                role=UserRole(pending_user['role']),
                organization=pending_user['organization']
            )
            user.set_password(pending_user['password'])
            db.session.add(user)
            db.session.commit()
            
            # Clear session data
            session.pop('pending_user', None)
            
            # Log in the user
            login_user(user)
            flash("Email verified! Welcome! Account created.", "success")
            return redirect(url_for("opportunities.home"))
        else:
            flash(message, "error")
    
    return render_template("auth/verify_email.html", form=form, email=pending_user['email'])


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for("opportunities.home"))
    
    email = request.form.get('email')
    if not email:
        flash("Email address required.", "error")
        return redirect(url_for("auth.signup"))
    
    # Create new verification record and send email
    verification_code = create_verification_record(email)
    if verification_code:
        if send_verification_email(email, verification_code):
            flash("New verification code sent to your email.", "info")
        else:
            flash("Failed to send verification email. Please try again.", "error")
    else:
        flash("Failed to create verification record. Please try again.", "error")
    
    return redirect(url_for("auth.verify_email"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
