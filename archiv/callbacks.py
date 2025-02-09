import pandas as pd
import openai
import plotly.graph_objs as go
from dash import Output, Input, State
from data_fetching import fetch_stock_data
from config import apikeys

# Load OpenAI API Key
chatgpt_api_key = apikeys["chatgpt"]

def register_callbacks(app):
    """Register all Dash callbacks."""

    # Callback for updating stock chart
    @app.callback(
        Output("stock-chart", "figure"),
        Input("stock-dropdown", "value"),
        Input("time-range-dropdown", "value")
    )
    def update_stock_chart(symbol, time_range):
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
        if not user_input:
            return "Please enter a message."

        try:
            client = openai.OpenAI(api_key=chatgpt_api_key)
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": user_input}]
            )
            return response.choices[0].message.content
        except openai.OpenAIError as e:
            return f"Error with ChatGPT API: {str(e)}"
