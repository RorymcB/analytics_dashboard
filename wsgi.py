from app import server  # Import Flask server instance

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8050, debug=True)
