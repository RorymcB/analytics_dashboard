import logging
from dash import Output, Input, State, html
import plotly.graph_objs as go
from openai import OpenAI
from data_fetching import fetch_stock_data
from config import apikeys
from database import db
from models import ChatMessage
from flask import session, current_app
from flask_login import current_user
from data_fetching import fetch_historical_stock_data
from layout import get_layout, get_navbar
from alpha_vantage.timeseries import TimeSeries

chatgpt_api_key = apikeys["chatgpt"]
alpha_vantage_api_key = apikeys["alpha_vantage"]

def register_callbacks(app, server):
    """Register Dash callbacks for stock chart, chat AI, and dark mode toggle."""

    # Stock Chart Update
    @app.callback(
        Output("stock-chart", "figure"),
        Input("stock-dropdown", "value")
    )
    def update_stock_chart(symbol):
        """Fetch stock price data from Alpha Vantage."""
        ts = TimeSeries(key=alpha_vantage_api_key, output_format="pandas")
        try:
            data, meta_data = ts.get_daily(symbol=symbol, outputsize="compact")
            data = data.rename(columns={"4. close": "Close"})
            data.index = data.index.astype(str)  # Convert index to string for plotting

            return {
                'data': [
                    go.Scatter(
                        x=data.index,
                        y=data["Close"],
                        mode='lines',
                        name=symbol
                    )
                ],
                'layout': go.Layout(
                    title=f"Stock Price Over Time ({symbol})",
                    xaxis={'title': "Date"},
                    yaxis={'title': "Closing Price (USD)"},
                    hovermode='closest'
                )
            }
        except Exception as e:
            return {
                'data': [],
                'layout': go.Layout(title=f"Error: {e}")
            }

    client = OpenAI(api_key=chatgpt_api_key)  # ✅ Initialize OpenAI Client
    # Register Dash callbacks including user-based chat storage.
    @app.callback(
        Output("chat-response", "children"),
        Output("chat-history", "children"),
        Input("send-button", "n_clicks"),
        State("chat-input", "value"),
        prevent_initial_call=True
    )

    def chat_with_gpt(n_clicks, user_input):
        """Send user input to ChatGPT and update chat history."""
        with server.app_context():  # ✅ Ensure we're in Flask context
            if not session.get("user_id"):
                return "Please log in to use chat.", []

            user_id = session["user_id"]
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": user_input}]
                )
                bot_response = response.choices[0].message.content

                chat_message = ChatMessage(user_id=user_id, user_message=user_input, bot_response=bot_response)
                db.session.add(chat_message)
                db.session.commit()

                return bot_response, get_chat_history(user_id)
            except Exception as e:
                return f"Error: {str(e)}", []

    def get_chat_history(user_id):
        """Retrieve user-specific chat history from database."""
        with server.app_context():  # ✅ Ensure we're in Flask context
            messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
            return [html.Div([
                html.P(f"🧑‍💻 {msg.user_message}", className="chat-user"),
                html.P(f"🤖 {msg.bot_response}", className="chat-bot")
            ]) for msg in messages]

    # Dark Mode Toggle
    @app.callback(
        Output("main-container", "className"),
        Output("theme-store", "data"),
        Input("theme-toggle", "value"),
        State("theme-store", "data")
    )
    def toggle_dark_mode(toggle_value, stored_theme):
        """Switch between light and dark mode."""
        if "dark" in toggle_value:
            return "dark-theme", {"theme": "dark"}
        return "light-theme", {"theme": "light"}

    # Update navbar with login/out
    @app.callback(
        Output("navbar", "children"),
        [Input("progress-interval", "n_intervals"),
        Input("login-state-update", "data")]
    )
    def update_navbar(n_intervals):
        logging.info(f"Navbar update triggered! Current session: {session.items()}")
        """Update navbar dynamically to reflect login/logout status."""
        user_id = session.get("user_id")
        if user_id:
            logging.info(f"Updating navbar for logged-in user: {session.get('username')}")
            return get_navbar()
        else:
            logging.info("Updating navbar for guest user.")
            return get_navbar()

    @app.callback(
        Output("admin-panel", "children"),
        Input("theme-store", "data")
    )
    def show_admin_panel(_):
        if session.get("user_id") and session.get("is_admin"):
            return html.Div([
                html.H2("🔧 Admin Panel"),
                html.P("Manage users, chats, and settings here."),
            ])
        return html.Div()


    @app.callback(
        Output("fetch-status", "children"),
        Input("fetch-button", "n_clicks"),
        State("stock-input", "value"),
        prevent_initial_call=True
    )
    def fetch_stock_data(n_clicks, symbol):
        """Fetch historical stock data when the button is clicked."""
        if not symbol:
            return "Please enter a stock symbol."

        with server.app_context():
            session["progress"] = "Starting fetch..."
            session["cancel_fetch"] = False  # ✅ Reset cancel flag
            fetch_historical_stock_data(symbol.upper())
            return session.get("progress", "Fetching data...")

    @app.callback(
        Output("fetch-status", "children"),
        Input("progress-interval", "n_intervals")
    )
    def update_progress(n_intervals):
        """Update the fetch progress display."""
        return session.get("progress", "Waiting for request...")

    @app.callback(
        Output("fetch-status", "children"),
        Input("cancel-button", "n_clicks"),
        prevent_initial_call=True
    )
    def cancel_fetch(n_clicks):
        """Cancel the stock data fetching process."""
        session["cancel_fetch"] = True  # ✅ Set cancel flag
        return "Fetching canceled by user."