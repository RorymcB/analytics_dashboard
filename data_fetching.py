import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from config import apikeys
from models import Stock, StockPrice
import yfinance as yf
from database import db
from decimal import Decimal
from datetime import datetime
from flask import session, current_app
from sqlalchemy import text
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

    print(f"Checking data for {symbol}...")

    # Check if the stock already exists
    stock_obj = Stock.query.filter_by(symbol=symbol).first()

    if stock_obj:
        # Check if data exists in stock_price table
        latest_entry = db.session.execute(
            text("SELECT MAX(date) FROM stock_price WHERE stock_id = :stock_id"),
            {"stock_id": stock_obj.id}
        ).scalar()

        if latest_entry:
            print(f"Data for {symbol} already exists up to {latest_entry}. Skipping fetch.")
            return f"Data for {symbol} already exists up to {latest_entry}. No new data fetched."

    print(f"Fetching historical data for {symbol}...")

    stock = yf.Ticker(symbol)
    df = stock.history(period="max")

    if df.empty:
        print(f"No data found for {symbol}")
        return f"No data found for {symbol}"

    # Store stock metadata if it doesn't exist
    if not stock_obj:
        stock_obj = Stock(symbol=symbol, name=stock.info.get("longName", symbol))
        db.session.add(stock_obj)
        db.session.commit()

    from models import StockPrice  # Import inside function to avoid circular imports

    # Insert stock price data
    for date, row in df.iterrows():
        volume = row["Volume"]

        # Ensure volume is stored as an integer
        if isinstance(volume, float) or isinstance(volume, Decimal):
            volume = int(volume)

        # ✅ Check if this date already exists in the database
        existing_entry = StockPrice.query.filter_by(stock_id=stock_obj.id, date=date.date()).first()
        if existing_entry:
            continue  # ✅ Skip if this date already exists

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
    print(f"Data for {symbol} inserted successfully!")
    return f"Historical data for {symbol} inserted successfully!"


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
