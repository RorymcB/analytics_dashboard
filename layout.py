import logging
import dash
from dash import dcc, html, dash_table
from data_fetching import get_available_stocks
from flask import session

def get_navbar():
    """Return a dynamic navigation bar for users and admins."""
    user_id = session.get("user_id")
    is_admin = session.get("is_admin")

    logging.info(f"Navbar update triggered! Session Data: {session.items()}")

    nav_links = [html.A("📈 Dashboard", href="/dashboard/", className="navbar-title")]

    if user_id:
        nav_links.append(html.A("👤 Accounts", href="/auth/accounts", className="navbar-link"))  # ✅ Now visible for all users
        if is_admin:
            nav_links.append(html.A("🔧 Admin Panel", href="/admin", className="navbar-link"))
        nav_links.append(html.A("Logout", href="/auth/logout", className="logout-button"))
    else:
        nav_links.append(html.A("Login", href="/auth/login", className="login-button"))
        nav_links.append(html.A("Register", href="/auth/register", className="register-button"))

    return html.Div(nav_links, className="navbar")

def get_layout():
    """Return the Dash layout with stock graphs and AI chat on one page."""
    return html.Div([
        # Store to Save Theme Selection
        dcc.Store(id="theme-store", data={"theme": "light"}),
        dcc.Store(id="login-state-update"),  # ✅ Track login state manually

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

        # Navigation Bar (Now Dynamic)
        html.Div(id="navbar"),  # ✅ Navbar will update dynamically

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

            # Local Stock Data Plot Section
            html.Div([
                html.H3("Select Stocks to Compare"),
                dcc.Dropdown(
                    id="local-stock-dropdown",
                    options=[],  # ✅ Load dynamically via callback
                    placeholder="Select stocks",
                    className="dropdown",
                    multi=True  # ✅ Allow multiple selections
                ),
                html.Button("Refresh Dropdown", id="refresh-dropdown-btn", n_clicks=0),
                dcc.Graph(id="local-stock-chart")
            ], className="plot-container"),

            # Stock Data Fetching Section
            html.Div([
                html.H3("Download Historical Stock Data"),
                dcc.Input(id="stock-input", type="text", placeholder="Enter Stock Symbol", className="input-field"),
                html.Button("Fetch Data", id="fetch-button", className="fetch-button"),
                html.Div(id="fetch-status", className="status-output")  # Output field for progress
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


def get_accounts_layout():
    """Return the Dash layout for the Accounts page."""
    return html.Div([
        # Back to Dashboard Link
        html.Div([
            html.A("⬅ Back to Dashboard", href="/dashboard/", className="back-link")
        ], className="navigation-container"),

        html.H1("🔑 User Accounts & 📊 Transaction Data", className="header"),

        # Transactions Table
        dash_table.DataTable(
            id="accounts-table",
            columns=[
                {"name": "ID", "id": "id"},
                {"name": "Username", "id": "username"},
                {"name": "Email", "id": "email"},
                {"name": "Role", "id": "role"}
            ],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left"},
        ),

        html.Button("Refresh Data", id="refresh-accounts-btn", n_clicks=0, className="refresh-button"),

        html.Hr(),

        html.Div(id="admin-actions", className="admin-actions"),  # ✅ Only shown for admins

        # Table to display transactions
        dash_table.DataTable(
            id="transactions-table",
            columns=[
                {"name": "ID", "id": "transaction_id"},
                {"name": "Buchungstag", "id": "Buchungstag"},
                {"name": "Valutadatum", "id": "Valutadatum"},
                {"name": "Beguenstigter", "id": "Beguenstigter"},
                {"name": "IBAN", "id": "Kontonummer_IBAN"},
                {"name": "Betrag (€)", "id": "Betrag"},
                {"name": "Category", "id": "category"}
            ],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left"},
        ),

        html.Button("Refresh Transactions", id="refresh-transactions-btn", n_clicks=0, className="refresh-button"),

        html.Hr(),

        # Transaction Plots
        html.H3("📈 Transaction Data Visualizations"),
        html.Div([
            html.H3("📊 Interactive Transaction Chart"),

            html.Label("Select Chart Type:"),
            dcc.RadioItems(
                id="chart-type-radio",
                options=[
                    {"label": "Line", "value": "line"},
                    {"label": "Stacked Area", "value": "area"},
                    {"label": "Stacked Bar", "value": "bar"},
                ],
                value="line",
                labelStyle={"display": "inline-block", "margin-right": "15px"}
            ),

            html.Br(),

            html.Label("Select Time Range:"),
            dcc.DatePickerRange(
                id="date-picker-range",
                display_format="YYYY-MM-DD"
            ),

            html.Div([
                html.Button("Last Day", id="btn-last-day", n_clicks=0),
                html.Button("Last Week", id="btn-last-week", n_clicks=0),
                html.Button("Last Month", id="btn-last-month", n_clicks=0),
                html.Button("Last Year", id="btn-last-year", n_clicks=0)
            ], style={"margin-top": "10px"}),

            dcc.Graph(id="transaction-plot"),
            dcc.Graph(id="transaction-pie")
        ], className="plot-container"),

        dcc.Graph(id="line-chart"),
        dcc.Graph(id="stacked-area-chart"),
        dcc.Graph(id="stacked-bar-chart"),
        dcc.Graph(id="pie-chart"),

    ])
