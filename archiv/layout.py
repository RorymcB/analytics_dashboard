import dash
from dash import dcc, html

# Time Range Options
TIME_RANGE_OPTIONS = {
    "7d": "Last 7 Days",
    "1m": "Last 1 Month",
    "3m": "Last 3 Months",
    "6m": "Last 6 Months",
    "1y": "Last 1 Year",
    "max": "Max Available"
}

def get_layout():
    """Return the Dash layout."""
    return html.Div(children=[
        html.H1("Stock Market & AI Chat Dashboard", style={'textAlign': 'center'}),

        # Stock Selection Controls
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
                style={"width": "50%"}
            ),
        ], style={'textAlign': 'center', 'marginBottom': '10px'}),

        # Time Range Selection
        html.Div([
            html.Label("Select Time Range:"),
            dcc.Dropdown(
                id="time-range-dropdown",
                options=[{"label": v, "value": k} for k, v in TIME_RANGE_OPTIONS.items()],
                value="3m",
                clearable=False,
                style={"width": "50%"}
            ),
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),

        # Stock Price Line Chart
        dcc.Graph(id='stock-chart'),

        # ChatGPT Section
        html.Div([
            html.H3("Chat with AI", style={'marginTop': '20px'}),
            dcc.Input(id="chat-input", type="text", placeholder="Ask me anything...", style={'width': '70%'}),
            html.Button("Send", id="send-button", n_clicks=0),
            html.Div(id="chat-response", style={'marginTop': '20px', 'padding': '10px', 'border': '1px solid black'})
        ])
    ])
