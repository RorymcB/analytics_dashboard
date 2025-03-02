import logging
import pandas as pd
from dash import Output, Input, State, html, no_update, dcc
import plotly.graph_objs as go
from openai import OpenAI
from data_fetching import fetch_stock_data, fetch_historical_stock_data, fetch_local_stock_data, get_available_stocks, get_all_accounts, get_transaction_data
from plots import generate_line_chart, generate_stacked_area_chart, generate_stacked_bar_chart, generate_pie_chart
from config import apikeys
from database import db
from models import ChatMessage, User
from flask import session, current_app
from flask_login import current_user

chatgpt_api_key = apikeys["chatgpt"]

# def generate_sample_accounts():
#     """Generate fake account data for non-admin users."""
#     sample_data = [
#         {
#             "id": i + 1,
#             "username": fake.user_name(),
#             "email": fake.email(),
#             "role": "User"
#         }
#         for i in range(10)
#     ]
#     return pd.DataFrame(sample_data)


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
        # df_stock.to_excel(f'df_{symbol}.xlsx')
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
        [Input("send-button", "n_clicks"), Input("chat-input", "n_submit")],  # ✅ Detect Enter key
        State("chat-input", "value"),
        prevent_initial_call=True
    )

    def chat_with_gpt(n_clicks, n_submit, user_input):
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
        Input("login-state-update", "data")  # ✅ Only updates when login state changes
    )
    def update_navbar(login_state):
        """Update navbar dynamically when login/logout occurs."""
        user_id = session.get("user_id")
        is_admin = session.get("is_admin")

        logging.info(f"Navbar update triggered! Session Data: {session.items()}")

        if not user_id:
            return html.Div([
                html.A("📈 Dashboard", href="/dashboard/", className="navbar-title"),
                html.A("Login", href="/auth/login", className="login-button"),
                html.A("Register", href="/auth/register", className="register-button")
            ], className="navbar")

        nav_links = [html.A("📈 Dashboard", href="/dashboard/", className="navbar-title")]
        # if is_admin:
        nav_links.append(html.A("👤 Accounts", href="/accounts", className="navbar-link"))
        nav_links.append(html.A("Logout", href="/auth/logout", className="logout-button"))

        return html.Div(nav_links, className="navbar")

    @app.callback(
        Output("fetch-status", "children"),
        [Input("fetch-button", "n_clicks"), Input("stock-input", "n_submit")],  # ✅ Add n_submit
        State("stock-input", "value"),
        prevent_initial_call=True
    )
    def fetch_historical_data(n_clicks, n_submit, symbol):
        """Fetch historical stock data when the button is clicked."""
        if not symbol:
            return "Please enter a stock symbol."

        with server.app_context():
            session["progress"] = "Starting fetch..."
            fetch_historical_stock_data(symbol.upper())
            return session.get("progress", "Fetching data...")

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

    @app.callback(
        Output("accounts-table", "data"),
        Input("refresh-accounts-btn", "n_clicks")
    )
    def refresh_accounts(n_clicks):
        """Fetch user accounts only if admin, otherwise return empty list."""
        if session.get("is_admin"):
            df = get_all_accounts()
        else:
            df = pd.DataFrame()  # No data for non-admins

        return df.to_dict("records") if not df.empty else []

    @app.callback(
        Output("admin-actions", "children"),
        Input("refresh-accounts-btn", "n_clicks")
    )
    def show_admin_controls(n_clicks):
        """Display admin controls only if the user is an admin."""
        if not session.get("is_admin"):
            return ""  # ✅ Regular users see nothing

        return html.Div([
            html.Label("User ID (For Update/Delete):"),
            dcc.Input(id="user-id-input", type="number", placeholder="Enter User ID", className="input-field"),

            html.Label("New Role (Admin/User):"),
            dcc.Dropdown(
                id="role-dropdown",
                options=[
                    {"label": "Admin", "value": True},
                    {"label": "User", "value": False}
                ],
                placeholder="Select role"
            ),

            html.Button("Update Role", id="update-role-btn", n_clicks=0, className="update-button"),
            html.Button("Delete User", id="delete-user-btn", n_clicks=0, className="delete-button"),
            html.Div(id="account-action-status", className="status-output")  # ✅ Status messages
        ])

    @app.callback(
        Output("account-action-status", "children"),
        [Input("update-role-btn", "n_clicks"), Input("delete-user-btn", "n_clicks")],
        [State("user-id-input", "value"), State("role-dropdown", "value")]
    )
    def modify_user(n_update, n_delete, user_id, new_role):
        """Update or delete a user account."""
        if not session.get("is_admin"):
            return "Access Denied: Only admins can modify accounts."

        if n_update > 0:
            if not user_id or new_role is None:
                return "Please provide both User ID and Role to update."

            with server.app_context():
                user = User.query.get(user_id)
                if not user:
                    return f"User ID {user_id} not found."

                user.is_admin = new_role
                db.session.commit()
                logging.info(f"Updated user {user.username} to {'Admin' if new_role else 'User'}.")
                return f"User {user.username} role updated successfully."

        if n_delete > 0:
            if not user_id:
                return "Please provide a User ID to delete."

            with server.app_context():
                user = User.query.get(user_id)
                if not user:
                    return f"User ID {user_id} not found."

                db.session.delete(user)
                db.session.commit()
                logging.info(f"Deleted user {user.username}.")
                return f"User {user.username} deleted successfully."

        return no_update  # ✅ If no action is taken, keep UI unchanged

    @app.callback(
        Output("transactions-table", "data"),
        Input("refresh-transactions-btn", "n_clicks")
    )
    def refresh_transactions(n_clicks):
        """Fetch transaction data for admins and users."""
        logging.info(f"User {session.get('username')} is fetching transaction data.")

        df = get_transaction_data()

        return df.to_dict("records") if not df.empty else []

    @app.callback(
        Output("line-chart", "figure"),
        Output("stacked-area-chart", "figure"),
        Output("stacked-bar-chart", "figure"),
        Output("pie-chart", "figure"),
        Input("refresh-transactions-btn", "n_clicks")
    )
    def update_transaction_plots(n_clicks):
        """Update all transaction data visualizations."""
        logging.info("Updating transaction data visualizations.")

        return (
            generate_line_chart(),
            generate_stacked_area_chart(),
            generate_stacked_bar_chart(),
            generate_pie_chart()
        )
