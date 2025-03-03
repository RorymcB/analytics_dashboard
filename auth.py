import logging
import pandas as pd
from flask import Blueprint, render_template, redirect, request, session, url_for, flash, jsonify
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from database import db
from models import User
from layout import get_accounts_layout
from config import MAIL_USERNAME, MAIL_PASSWORD
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, template_folder="templates")

login_manager = LoginManager()
login_manager.login_view = "auth.login"

# Flask-Mail Setup
mail = Mail()  # ✅ Fix: Define Flask-Mail object
s = URLSafeTimedSerializer("supersecretkey") #ToDo


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login route."""
    logging.info("Accessed /login route")  # ✅ Log login page access

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            logging.info(f"User {username} logged in successfully.")
            return redirect("/dashboard/")
        else:
            logging.warning(f"Failed login attempt for username: {username}")
            return "Invalid login credentials. Try again."

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    """User logout route."""
    try:
        username = session.get("username", "Unknown")
        logout_user()  # ✅ Correct Flask-Login logout function
        session.clear()  # ✅ Ensures all session data is removed
        logging.info(f"User {username} logged out.")
        return redirect("/dashboard/")  # ✅ Redirect to dashboard after logout
    except Exception as e:
        logging.error(f"Error logging out: {e}")
        return "Error logging out", 500

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration with email verification."""
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        # ✅ Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("This email is already registered. Please log in or use another email.", "error")
            return redirect(url_for("auth.register"))  # ✅ Redirect to registration page

        new_user = User(username=username, email=email, password=password, is_verified=False)
        db.session.add(new_user)

        try:
            db.session.commit()
        except Exception as e:
            logging.error(f"Error committing new user: {e}")
            db.session.rollback()  # ✅ Prevent database corruption
            return "An error occurred. Please try again."

        # ✅ Send email verification
        token = s.dumps(email, salt="email-confirm")
        msg = Message("Confirm Your Email", recipients=[email])
        msg.body = f"Click the link to verify your email: {url_for('auth.confirm_email', token=token, _external=True)}"
        mail.send(msg)

        return "A verification email has been sent!"

    return render_template("register.html")


@auth_bp.route("/confirm_email/<token>")
def confirm_email(token):
    """Confirm email using a secure token."""
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)  # ✅ Decode the token
        logging.info(f"Decoded email from token: {email}")  # ✅ Debugging log

        user = User.query.filter_by(email=email).first()

        if not user:
            logging.warning(f"Email verification failed: {email} not found in database")
            return "Invalid verification link or user does not exist.", 400

        if user.is_verified:
            return "Your email is already verified. You can log in now."

        user.is_verified = True
        db.session.commit()
        return "Email verified successfully! You can now log in."

    except SignatureExpired:
        return "The verification link has expired! Please request a new one.", 400

    except Exception as e:
        logging.error(f"Error verifying email: {e}")
        return "An error occurred while verifying your email. Please try again later.", 500


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt="password-reset")
            msg = Message("Reset Your Password", recipients=[email])
            msg.body = f"Click the link to reset your password: {url_for('auth.reset_password', token=token, _external=True)}"
            mail.send(msg)
            return "A password reset email has been sent!"
    return render_template("forgot_password.html")

@auth_bp.route("/resend_verification", methods=["POST"])
def resend_verification():
    email = request.form["email"]
    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified:
        token = s.dumps(email, salt="email-confirm")
        msg = Message("Confirm Your Email", recipients=[email])
        msg.body = f"Click the link to verify your email: {url_for('auth.confirm_email', token=token, _external=True)}"
        mail.send(msg)
        return "A new verification email has been sent!"
    return "Email not found or already verified."

@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Reset password using a secure token."""
    try:
        email = s.loads(token, salt="password-reset", max_age=3600)
        user = User.query.filter_by(email=email).first()
        if request.method == "POST":
            new_password = generate_password_hash(request.form["password"])
            user.password = new_password
            db.session.commit()
            return "Password reset successful! You can now login."

        return render_template("reset_password.html")
    except SignatureExpired:
        return "The password reset link has expired!"

@auth_bp.route("/admin_dashboard")
@login_required
def admin_dashboard():
    """Admin-only dashboard."""
    if not session.get("is_admin"):
        return "Access Denied: Admins only!", 403
    return render_template("admin_dashboard.html")

@auth_bp.route("/set_login_state", methods=["POST"])
def set_login_state():
    """Force Dash to recognize login state changes."""
    return jsonify({"status": "success"})

# def generate_sample_accounts():
#     """Generate sample user data for non-admins."""
#     sample_data = [
#         {
#             "id": i + 1,
#             "username": fake.user_name(),
#             "email": fake.email(),
#             "role": "User"
#         }
#         for i in range(10)
#     ]
#     return pd.DataFrame(sample_data)  # ✅ Returns a Pandas DataFrame for easy handling


@auth_bp.route("/accounts", endpoint="accounts_page")  # ✅ Unique endpoint name
@login_required
def accounts():
    """Render the accounts page differently for admins and users."""

    logging.info(f"User {session.get('username')} accessed the Accounts page.")

    return get_accounts_layout()  # ✅ Returns Dash layout for all users