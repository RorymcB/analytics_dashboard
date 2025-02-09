from database import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for authentication."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # Email verification
    is_admin = db.Column(db.Boolean, default=False)  # Admin access
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    """Stores chat messages per user."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Stock(db.Model):
    """Stores stock data."""
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class UserStock(db.Model):
    """Tracks which users are following which stocks (Many-to-Many)."""
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), primary_key=True)
