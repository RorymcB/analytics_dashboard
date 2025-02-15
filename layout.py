import logging
import dash
from dash import dcc, html
from flask import session


def get_navbar():
    """Return the navigation bar with login/logout options."""
    user_id = session.get("user_id")

    logging.info(f"Session Data: {session.items()}")  # ✅ Debug session contents

    if user_id:
        logging.info(f"Rendering navbar for logged-in user: {session.get('username')}")
        return html.Div([
            html.A("📈 Stock Market & AI Chat Dashboard", href="/", className="navbar-title"),
            html.A("Logout", href="/logout", className="logout-button"),
        ], className="navbar")
    else:
        logging.info("Rendering navbar for guest user.")
        return html.Div([
            html.A("📈 Stock Market & AI Chat Dashboard", href="/", className="navbar-title"),
            html.A("Login", href="/login", className="login-button"),
            html.A("Register", href="/register", className="register-button")
        ], className="navbar")

def get_admin_panel():
    """Return the admin dashboard panel."""
    return html.Div([
        html.H2("🔧 Admin Panel"),
        html.P("Manage users, stock data, and visualize financial transactions."),
        dcc.Graph(id="financial-chart"),  # ✅ Placeholder for financial data visualization
    ], className="admin-panel")


def get_layout():
    """Return the Dash layout with stock graphs and AI chat on one page."""
    return html.Div([
        # Store to Save Theme Selection
        dcc.Store(id="theme-store", data={"theme": "light"}),
        dcc.Store(id="login-state-update"),  # ✅ New hidden store to track login state

        # Dark Mode Toggle
        html.Div([
            html.Label("🌙 Toggle Dark Mode"),
            dcc.Checklist(
                id="theme-toggle",
                options=[{"label": "", "value": "dark"}],
                value=[],  # Default to light mode
                className="toggle-container"
            )
        ], className="theme-toggle"),

        # Navigation Bar (Login / Logout)
        html.Div(id="navbar", className="navbar"),
        dcc.Interval(id="progress-interval", interval=5000, n_intervals=0),

        html.Div(id="admin-panel", className="admin-container"),

        # Page Content
        html.Div([
            html.H1("📊 Stock Market & AI Chat Dashboard", className="header"),

            # Stock Selection Dropdown
            html.Div([
                html.Label("Select Stock Symbol:"),
                dcc.Dropdown(
                    id="stock-dropdown",
                    options=[
                        {"label": "Apple (AAPL)", "value": "AAPL"},
                        {"label": "Google (GOOGL)", "value": "GOOGL"},
                        {"label": "Microsoft (MSFT)", "value": "MSFT"},
                        {"label": "Tesla (TSLA)", "value": "TSLA"},
                        {"label": "Amazon (AMZN)", "value": "AMZN"}
                    ],
                    value="AAPL",
                    clearable=False,
                    className="dash-dropdown"
                ),
            ], className="dropdown-container"),

            # Stock Chart
            dcc.Graph(id='stock-chart', className="graph-container"),

            # Stock Data Fetching Section
            html.Div([
                html.H3("Download Historical Stock Data"),
                dcc.Input(id="stock-input", type="text", placeholder="Enter Stock Symbol", className="input-field"),
                html.Button("Fetch Data", id="fetch-button", className="fetch-button"),
                html.Button("Cancel", id="cancel-button", className="cancel-button"),  # ✅ Cancel Button
                html.Div(id="fetch-status", className="status-output"),  # ✅ Progress Output
                dcc.Interval(id="progress-interval", interval=2000, n_intervals=0)  # ✅ Auto-refresh progress every 2s
            ], className="fetch-container"),

            # Chat Section
            html.Div([
                html.H2("💬 AI Chat Assistant", className="chat-header"),
                dcc.Input(id="chat-input", type="text", placeholder="Ask ChatGPT...", className="chat-input"),
                html.Button("Send", id="send-button", className="send-button"),
                html.Div(id="chat-response", className="chat-response"),
                html.Div(id="chat-history", className="chat-history")
            ], className="chat-container"),
        ], className="content-container")
    ], id="main-container")
