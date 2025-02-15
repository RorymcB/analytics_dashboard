import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from config import apikeys
from models import Stock
import yfinance as yf
from database import db
from decimal import Decimal
from datetime import datetime
from flask import session

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
    """Fetch stock prices only if missing."""
    session["progress"] = f"Checking database for {symbol}..."

    stock_obj = Stock.query.filter_by(symbol=symbol).first()

    if stock_obj:
        latest_entry = db.session.execute(
            "SELECT MAX(date) FROM stock_price WHERE stock_id = :stock_id",
            {"stock_id": stock_obj.id}
        ).scalar()

        if latest_entry:
            session["progress"] = f"Data for {symbol} already exists. Skipping fetch."
            return

    session["progress"] = f"Fetching data for {symbol} from Yahoo Finance..."

    stock = yf.Ticker(symbol)
    df = stock.history(period="max")

    if df.empty:
        session["progress"] = f"No data found for {symbol}"
        return

    if not stock_obj:
        stock_obj = Stock(symbol=symbol, name=stock.info.get("longName", symbol))
        db.session.add(stock_obj)
        db.session.commit()

    from models import StockPrice

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
    session["progress"] = f"New data for {symbol} added successfully!"