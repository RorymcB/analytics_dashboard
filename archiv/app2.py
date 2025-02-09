import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import openai
from alpha_vantage.timeseries import TimeSeries
from keys import apikeys  # Ensure you have a keys.py file with your API keys

# Load API keys
chatgpt_api_key = apikeys.get('chatgpt', 'your_openai_api_key')
av_api_key = apikeys.get('alpha_vantage', 'your_alpha_vantage_api_key')

# Function to fetch stock data from Alpha Vantage
def fetch_stock_data(symbol="AAPL"):
    """Fetch daily stock price data from Alpha Vantage API."""
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

# Initialize Dash app
app = dash.Dash(__name__)

# Default stock data (AAPL)
df_stock = fetch_stock_data()

# Time range options
TIME_RANGE_OPTIONS = {
    "7d": "Last 7 Days",
    "1m": "Last 1 Month",
    "3m": "Last 3 Months",
    "6m": "Last 6 Months",
    "1y": "Last 1 Year",
    "max": "Max Available"
}

# App Layout
app.layout = html.Div(children=[
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

# Callback for Stock Chart Update
@app.callback(
    Output("stock-chart", "figure"),
    Input("stock-dropdown", "value"),
    Input("time-range-dropdown", "value")
)
def update_stock_chart(symbol, time_range):
    """Update stock chart based on selected stock and time range."""
    df_stock = fetch_stock_data(symbol)

    if df_stock.empty:
        return {
            'data': [],
            'layout': go.Layout(
                title=f"Stock Price Over Time ({symbol})",
                xaxis={'title': "Date"},
                yaxis={'title': "Closing Price (USD)"},
                annotations=[{
                    "text": "No data available",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }]
            )
        }

    # Filter data based on selected time range
    today = df_stock.index.max()
    if time_range == "7d":
        df_stock = df_stock[df_stock.index >= today - pd.DateOffset(days=7)]
    elif time_range == "1m":
        df_stock = df_stock[df_stock.index >= today - pd.DateOffset(months=1)]
    elif time_range == "3m":
        df_stock = df_stock[df_stock.index >= today - pd.DateOffset(months=3)]
    elif time_range == "6m":
        df_stock = df_stock[df_stock.index >= today - pd.DateOffset(months=6)]
    elif time_range == "1y":
        df_stock = df_stock[df_stock.index >= today - pd.DateOffset(years=1)]

    # Create figure
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

# Callback for ChatGPT interaction
@app.callback(
    Output("chat-response", "children"),
    Input("send-button", "n_clicks"),
    State("chat-input", "value"),
    prevent_initial_call=True
)
def chat_with_gpt(n_clicks, user_input):
    """Send user input to ChatGPT and return response."""
    if not user_input:
        return "Please enter a message."

    try:
        client = openai.OpenAI(api_key=chatgpt_api_key)  # OpenAI API Client

        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Change model as needed
            messages=[{"role": "user", "content": user_input}]
        )

        return response.choices[0].message.content
    except openai.OpenAIError as e:
        return f"Error with ChatGPT API: {str(e)}"

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
