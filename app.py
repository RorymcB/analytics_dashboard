from flask import Flask, redirect
import dash
from flask_mail import Mail
from layout import get_layout
from callbacks import register_callbacks
from auth import auth_bp, login_manager, mail
from database import init_db, db
from config import MAIL_USERNAME, MAIL_PASSWORD

# Create Flask App
server = Flask(__name__)
server.config["SECRET_KEY"] = "supersecretkey"

# Email Configuration
server.config["MAIL_SERVER"] = "smtp.gmail.com"
server.config["MAIL_PORT"] = 587
server.config["MAIL_USE_TLS"] = True
server.config["MAIL_USERNAME"] = MAIL_USERNAME  # Change to your email
server.config["MAIL_PASSWORD"] = MAIL_PASSWORD  # Use App Password if using Gmail
server.config["MAIL_DEFAULT_SENDER"] = "noreply@analytics-dashboard.com"

# Initialize Flask Extensions
mail.init_app(server)  # ✅ Fix: Initialize Flask-Mail
init_db(server)
login_manager.init_app(server)
server.register_blueprint(auth_bp)

# Create Dash App
app = dash.Dash(__name__, server=server, routes_pathname_prefix="/dashboard/")
app.layout = get_layout()

# Register Dash Callbacks
register_callbacks(app, server)

# Redirect the root URL ("/") to the Dash app automatically
@server.route("/")
def index():
    return redirect("/dashboard/")

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8050, debug=True)
