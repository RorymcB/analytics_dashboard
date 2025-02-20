import logging
from dash import Output, Input, State, html
import plotly.graph_objs as go
from openai import OpenAI
from data_fetching import fetch_stock_data, fetch_historical_stock_data, fetch_local_stock_data, get_available_stocks
from config import apikeys
from database import db
from models import ChatMessage
from flask import session, current_app
from flask_login import current_user

chatgpt_api_key = apikeys["chatgpt"]

def register_callbacks(app, server):
    """Register Dash callbacks for stock chart, chat AI, and dark mode toggle."""

    # Stock Chart Update
    @app.callback(
        Output("stock-chart", "figure"),
        Input("stock-dropdown", "value"),
        prevent_initial_call=True
    )
    def update_stock_chart(symbol):
        print('symbol =', symbol)
        """Update stock chart based on selected stock."""
        df_stock = fetch_stock_data(symbol=symbol)
        df_stock.to_excel(f'df_{symbol}.xlsx')
        figure = {
            'data': [
                go.Scatter(
                    x=df_stock.index,
                    y=df_stock["Close"],
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
        return figure

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
        Input("theme-store", "data")
    )
    def update_navbar(_):
        """Update navbar with login/logout buttons."""
        with server.app_context():  # ✅ Ensure we're in Flask context
            if "user_id" in session:  # ✅ Check if a user is logged in
                return html.Div([
                    html.Span(f"Welcome, {session['username']}!", className="user-greeting"),
                    html.A("Logout", href="/auth/logout", className="logout-button")
                ], className="navbar-container")
            else:
                return html.Div([
                    html.A("Login", href="/auth/login", className="login-button"),
                    html.A("Register", href="/register", className="register-button")
                ], className="navbar-container")

    @app.callback(
        Output("fetch-status", "children"),
        Input("fetch-button", "n_clicks"),
        State("stock-input", "value"),
        prevent_initial_call=True
    )
    def fetch_historical_data(n_clicks, esymbol):
        """Fetch historical stock data when the button is clicked."""
        if not esymbol:
            return "Please enter a stock symbol."

        with server.app_context():  # ✅ Ensure Flask context is available
            result_message = fetch_historical_stock_data(esymbol.upper())  # Convert to uppercase
            return result_message

    @app.callback(
        Output("local-stock-chart", "figure"),
        Input("local-stock-dropdown", "value")  # ✅ Handle multiple selections
    )
    def update_local_stock_chart(symbols):
        """Update the plot when multiple stocks are selected."""
        if not symbols:
            return {"data": [], "layout": go.Layout(title="Select stocks to display data")}

        stock_data = fetch_local_stock_data(symbols)

        if not stock_data:
            return {"data": [], "layout": go.Layout(title="No data available")}

        traces = []
        for symbol, df in stock_data.items():
            if not df.empty:
                traces.append(go.Scatter(
                    x=df["Date"],
                    y=df["Close"],
                    mode="lines",
                    name=symbol
                ))

        figure = {
            "data": traces,
            "layout": go.Layout(
                title="Stock Price Comparison",
                xaxis={"title": "Date"},
                yaxis={"title": "Closing Price"},
                hovermode="closest"
            )
        }
        return figure

    @app.callback(
        Output("local-stock-dropdown", "options"),
        Output("local-stock-dropdown", "value"),  # ✅ Preserve selected values
        [Input("refresh-dropdown-btn", "n_clicks")],
        [State("local-stock-dropdown", "value")]  # ✅ Store current selection
    )
    def populate_stock_dropdown(n_clicks, selected_symbols):
        """Dynamically fetch stock symbols from the database while keeping selection."""
        logging.info("Running dropdown population callback...")

        stocks = get_available_stocks()
        logging.info(f"Fetched stocks: {stocks}")

        options = [{"label": stock["label"], "value": stock["value"]} for stock in stocks]

        # ✅ Preserve selection if still valid
        if selected_symbols:
            valid_selection = [symbol for symbol in selected_symbols if symbol in [s["value"] for s in stocks]]
            return options, valid_selection

        return options, None
