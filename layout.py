import dash
from dash import dcc, html

def get_layout():
    """Return the Dash layout with stock graphs and AI chat on one page."""
    return html.Div([
        # Store to Save Theme Selection
        dcc.Store(id="theme-store", data={"theme": "light"}),

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
