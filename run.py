"""Entry point.  Run with:  python run.py   (or: flask --app run <command>)"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug comes from FLASK_DEBUG in .env and defaults to OFF.
    # Binding to 127.0.0.1 keeps the dev server reachable from this machine only.
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
