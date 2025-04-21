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

def generate_transaction_plot(chart_type="line", date_range=None):
    df = get_transaction_data()
    if df.empty:
        return go.Figure()

    df["Buchungstag"] = pd.to_datetime(df["Buchungstag"])
    df = df.sort_values("Buchungstag")

    # Filter by date range
    if date_range:
        start_date, end_date = date_range
        df = df[(df["Buchungstag"] >= start_date) & (df["Buchungstag"] <= end_date)]

    # Calculate cumulative per category
    df["cumulative"] = df.groupby("category")["Betrag"].cumsum()

    # Calculate rolling balance across all categories
    df_balance = df.groupby("Buchungstag")["Betrag"].sum().cumsum().reset_index()
    df_balance.rename(columns={"Betrag": "Balance"}, inplace=True)

    # Plot by selected chart type
    if chart_type == "line":
        fig = px.line(df, x="Buchungstag", y="cumulative", color="category", title="Cumulative Transactions")
    elif chart_type == "area":
        fig = px.area(df, x="Buchungstag", y="cumulative", color="category", title="Stacked Area Chart")
    elif chart_type == "bar":
        fig = px.bar(df, x="Buchungstag", y="cumulative", color="category", barmode="stack", title="Stacked Bar Chart")
    else:
        fig = go.Figure()

    # Add rolling balance as a secondary trace
    fig.add_trace(go.Scatter(
        x=df_balance["Buchungstag"],
        y=df_balance["Balance"],
        mode="lines",
        name="Total Balance",
        line=dict(color="rgba(0, 0, 0, 0.4)", width=4, dash="solid"),
        hoverinfo="x+y"
    ))

    return fig


def generate_pie_chart_by_range(date_range=None):
    df = get_transaction_data()
    df.to_csv('pie_test.csv')
    if df.empty:
        return go.Figure()

    df["Buchungstag"] = pd.to_datetime(df["Buchungstag"])
    df = df.sort_values("Buchungstag")

    if date_range:
        start_date, end_date = date_range
        df = df[(df["Buchungstag"] >= start_date) & (df["Buchungstag"] <= end_date)]

    df = df.loc[df['category'] != 'Arbeit']
    df['Betrag'] = df['Betrag'] * -1

    df_grouped = df.groupby("category")["Betrag"].sum().reset_index()

    return px.pie(df_grouped, names="category", values="Betrag", title="Spending Distribution (Filtered)")
