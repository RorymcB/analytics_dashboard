import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from config import apikeys

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
