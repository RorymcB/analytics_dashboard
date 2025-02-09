import dash
from layout import get_layout
from callbacks import register_callbacks

# Initialize Dash App
app = dash.Dash(__name__)
app.layout = get_layout()

# Register callbacks
register_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
