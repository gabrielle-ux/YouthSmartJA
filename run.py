from app import create_app

# Create the app instance using the factory
app = create_app()

if __name__ == "__main__":
    # In development, we use debug=True to see errors and auto-restart
    app.run(debug=True, host='0.0.0.0', port=5000)
