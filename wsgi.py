from app import server as app  # Import Flask server instance

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
