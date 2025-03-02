from flask_sqlalchemy import SQLAlchemy
from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

def init_db(app):
    """Initialize MySQL database with Flask app."""
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Ensure foreign keys are enabled in SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()
