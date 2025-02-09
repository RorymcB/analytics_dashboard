from flask_sqlalchemy import SQLAlchemy
from config import SQLALCHEMY_DATABASE_URI

db = SQLAlchemy()

def init_db(app):
    """Initialize MySQL database with Flask app."""
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
