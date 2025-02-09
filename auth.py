from flask import Blueprint, render_template, redirect, request, session, url_for, flash
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from database import db
from models import User
from config import MAIL_USERNAME, MAIL_PASSWORD
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

login_manager = LoginManager()
login_manager.login_view = "auth.login"

# Flask-Mail Setup
mail = Mail()
s = URLSafeTimedSerializer("supersecretkey")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login route."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session["user_id"] = user.id  # ✅ Store user ID in session
            session["username"] = user.username  # ✅ Store username in session
            return redirect("/dashboard/")

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    """User logout route."""
    logout_user()
    session.pop("user_id", None)  # ✅ Remove user from session
    session.pop("username", None)
    return redirect("/")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration with email verification."""
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(email=email).first():
            return "Email already registered!"

        new_user = User(username=username, email=email, password=password, is_verified=False)
        db.session.add(new_user)
        db.session.commit()

        # Generate verification token
        token = s.dumps(email, salt="email-confirm")

        # Send verification email
        msg = Message("Confirm Your Email", recipients=[email])
        msg.body = f"Click the link to verify your email: {url_for('auth.confirm_email', token=token, _external=True)}"
        mail.send(msg)

        return "A verification email has been sent!"

    return render_template("register.html")

@auth_bp.route("/confirm_email/<token>")
def confirm_email(token):
    """Confirm email using a secure token."""
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)  # 1-hour expiry
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_verified = True
            db.session.commit()
            return "Email verified! You can now login."
    except SignatureExpired:
        return "The verification link has expired!"

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
