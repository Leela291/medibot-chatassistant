# backend/app.py
"""
Flask application entry point.
"""
import sys
import os

# Make project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask
from flask_cors import CORS
from backend.routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})   # allow React dev server

    register_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()
    print("🏥 MediBot backend starting on http://localhost:8000")
    app.run(host="0.0.0.0", port=5000, debug=True)
