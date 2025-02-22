import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from data_fetching import get_transaction_data

def generate_line_chart():
    """Generate a line chart for transaction amounts over time."""
    df = get_transaction_data()
    if df.empty:
        return go.Figure()

    df["Buchungstag"] = pd.to_datetime(df["Buchungstag"])
    df = df.sort_values("Buchungstag")

    fig = px.line(df, x="Buchungstag", y="Betrag", title="Transaction Amount Over Time", markers=True)
    return fig

def generate_stacked_area_chart():
    """Generate a stacked area chart for cumulative spending by category."""
    df = get_transaction_data()
    if df.empty:
        return go.Figure()

    df["Buchungstag"] = pd.to_datetime(df["Buchungstag"])
    df = df.sort_values("Buchungstag")

    fig = px.area(df, x="Buchungstag", y="Betrag", color="category",
                  title="Cumulative Spending Over Time (Stacked Area)")
    return fig

def generate_stacked_bar_chart():
    """Generate a stacked bar chart for spending by category over time."""
    df = get_transaction_data()
    if df.empty:
        return go.Figure()

    df["Buchungstag"] = pd.to_datetime(df["Buchungstag"])
    df = df.sort_values("Buchungstag")

    fig = px.bar(df, x="Buchungstag", y="Betrag", color="category",
                 title="Spending by Category Over Time (Stacked Bar)",
                 barmode="stack")
    return fig

def generate_pie_chart():
    """Generate a pie chart for total spending distribution by category."""
    df = get_transaction_data()
    if df.empty:
        return go.Figure()

    fig = px.pie(df, names="category", values="Betrag", title="Spending Distribution by Category")
    return fig
