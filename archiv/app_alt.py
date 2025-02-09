import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import requests
import pandas as pd
import openai
from alpha_vantage.timeseries import TimeSeries
from keys import apikeys

# API Keys
chatgpt_api_key = apikeys['chatgpt']
av_api_key = apikeys['alpha_vantage']

# Function to fetch Verbraucherpreisindex (CPI) data from Destatis API
def fetch_cpi_data():
    try:
        url = "https://www-genesis.destatis.de/genesisWS/rest/2020/data/table?username=your_username&password=your_password&name=61111-0001&area=all&format=json"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error fetching CPI data: {response.status_code}")
            return pd.DataFrame({"Date": [], "CPI": []})

        data = response.json()

        # Extract CPI values (adjust if API structure differs)
        time_series = []
        cpi_values = []

        for record in data.get("Object", {}).get("Content", {}).get("Values", []):
            time_series.append(record.get("Date"))
            cpi_values.append(float(record.get("Value", 0)))

        df = pd.DataFrame({"Date": pd.to_datetime(time_series), "CPI": cpi_values})
        df.sort_values("Date", inplace=True)

        return df
    except Exception as e:
        print(f"Error parsing CPI data: {e}")
        return pd.DataFrame({"Date": [], "CPI": []})

# Function to fetch stock data from Alpha Vantage
def fetch_stock_data(symbol="AAPL"):
    ts = TimeSeries(key=av_api_key, output_format="pandas")
    try:
        data, meta_data = ts.get_daily(symbol=symbol, outputsize="compact")
        data = data.rename(columns={"4. close": "Close"})
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()
        return data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return pd.DataFrame({"Date": [], "Close": []})

# Initialize Dash App
app = dash.Dash(__name__)

# Initial Fetch (Defaults: AAPL, CPI)
df_cpi = fetch_cpi_data()
df_stock = fetch_stock_data()

# Layout
app.layout = html.Div(children=[
    html.H1("Economic & Stock Dashboard", style={'textAlign': 'center'}),

    # CPI Line Chart
    dcc.Graph(
        id='cpi-chart',
        figure={
            'data': [
                go.Scatter(
                    x=df_cpi["Date"],
                    y=df_cpi["CPI"],
                    mode='lines',
                    name='CPI'
                )
            ],
            'layout': go.Layout(
                title="German Consumer Price Index (CPI)",
                xaxis={'title': "Date"},
                yaxis={'title': "Index Value"},
                hovermode='closest'
            )
        }
    ),

    html.H2("Stock Market Overview", style={'textAlign': 'center'}),

    # Dropdown for Stock Selection
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
    ], style={'textAlign': 'center'}),

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

# Callback for Dynamic Stock Chart Update
@app.callback(
    Output("stock-chart", "figure"),
    Input("stock-dropdown", "value")
)
def update_stock_chart(symbol):
    df_stock = fetch_stock_data(symbol)

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
