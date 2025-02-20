import logging
import dash
from dash import dcc, html
from data_fetching import get_available_stocks
from flask import session

def get_navbar():
    """Return a static navbar placeholder (updated dynamically via Dash callback)."""
    logging.info("Rendering navbar placeholder...")  # ✅ Debugging

    return html.Div(id="navbar", className="navbar")  # ✅ Placeholder for dynamic navbar updates

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
