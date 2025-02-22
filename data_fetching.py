import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from config import apikeys
from models import Stock, StockPrice, User
import yfinance as yf
from database import db
from decimal import Decimal
from datetime import datetime
from flask import session, current_app
from sqlalchemy import text
from yfinance.exceptions import YFRateLimitError
import logging

av_api_key = apikeys["alpha_vantage"]

def fetch_stock_data(symbol="AAPL"):
    """Fetch stock data from Alpha Vantage API."""
    ts = TimeSeries(key=av_api_key, output_format="pandas")
    try:
        data, _ = ts.get_daily(symbol=symbol, outputsize="full")
        data = data.rename(columns={"4. close": "Close"})
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()
        return data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame(columns=["Date", "Close"])


def fetch_historical_stock_data(symbol):
    """Fetch historical stock prices from Yahoo Finance if not already in database."""

    session["progress"] = f"Checking database for {symbol}..."

    stock_obj = Stock.query.filter_by(symbol=symbol).first()

    if stock_obj:
        latest_entry = db.session.execute(
            text("SELECT MAX(date) FROM stock_price WHERE stock_id = :stock_id"),
            {"stock_id": stock_obj.id}
        ).scalar()

        if latest_entry:
            session["progress"] = f"Data for {symbol} already exists up to {latest_entry}. Skipping fetch."
            return

    session["progress"] = f"Fetching historical data for {symbol}..."

    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period="max")

        if df.empty:
            session["progress"] = f"No data found for {symbol}."
            return

    except YFRateLimitError:
        session["progress"] = "Rate limit exceeded! Please wait and try again later."
        logging.warning("Yahoo Finance rate limit exceeded for fetching stock data.")
        return  # Stop processing

    if not stock_obj:
        stock_obj = Stock(symbol=symbol, name=stock.info.get("longName", symbol))
        db.session.add(stock_obj)
        db.session.commit()

    for date, row in df.iterrows():
        volume = int(row["Volume"]) if row["Volume"] else None

        existing_entry = StockPrice.query.filter_by(stock_id=stock_obj.id, date=date.date()).first()
        if existing_entry:
            continue

        price = StockPrice(
            stock_id=stock_obj.id,
            date=date.date(),
            open_price=row["Open"],
            high_price=row["High"],
            low_price=row["Low"],
            close_price=row["Close"],
            volume=volume
        )
        db.session.add(price)

    db.session.commit()
    session["progress"] = f"Historical data for {symbol} inserted successfully!"


def get_available_stocks():
    """Fetch unique stock symbols from the database within an app context."""
    with current_app.app_context():  # ✅ Ensure we are inside Flask app context
        stocks = db.session.query(Stock.symbol).distinct().all()

    stock_list = [stock.symbol for stock in stocks]
    logging.info(f"Fetched stocks: {stock_list}")  # ✅ Log stock symbols
    return stock_list


def fetch_local_stock_data(symbols):
    """Fetch stock price data from the database for the given symbols."""
    if not symbols:
        return {}

    with current_app.app_context():
        stock_data = {}
        for symbol in symbols:
            stock_id = db.session.query(Stock.id).filter(Stock.symbol == symbol).scalar()

            if not stock_id:
                continue  # Skip if stock is not found

            data = db.session.query(StockPrice.date, StockPrice.close_price) \
                .filter(StockPrice.stock_id == stock_id) \
                .order_by(StockPrice.date.asc()).all()

            df = pd.DataFrame(data, columns=["Date", "Close"])
            stock_data[symbol] = df  # ✅ Store each stock's data in a dictionary

    return stock_data


def get_available_stocks():
    """Fetch stock symbols and names from the database within an app context."""
    with current_app.app_context():
        stocks = db.session.query(Stock.symbol, Stock.name).distinct().all()

    return [{"label": f"{stock.name} ({stock.symbol})", "value": stock.symbol} for stock in stocks]


def get_all_accounts():
    """Fetch all user accounts from the database."""
    with current_app.app_context():
        users = User.query.all()

    data = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": "Admin" if user.is_admin else "User"
        }
        for user in users
    ]

    return pd.DataFrame(data)  # ✅ Convert to DataFrame for easy Dash integration

def get_transaction_data():
    """Fetch transaction data based on user role."""
    with current_app.app_context():
        if session.get("is_admin"):
            query = text("SELECT * FROM sparkasse")  # ✅ Admins see real data
        else:
            query = text("SELECT * FROM transactions")  # ✅ Regular users see sample data

        transactions = db.session.execute(query).fetchall()

    if not transactions:
        return pd.DataFrame()  # ✅ Return empty DataFrame if no data found

    df = pd.DataFrame(transactions, columns=[
        "transaction_id", "Buchungstag", "Valutadatum", "Beguenstigter", "Kontonummer_IBAN", "Betrag", "category"
    ])

    return df