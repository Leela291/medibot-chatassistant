import sys
import os
from dotenv import load_dotenv

# Make project root importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
load_dotenv()

from llm.config import OPENFDA_API_KEY

from flask import Flask
from flask_cors import CORS
from backend.routes import register_routes


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    register_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()

    print("🏥 MediBot backend starting on http://localhost:5000")
    print("FDA API key configured:", bool(OPENFDA_API_KEY))

    app.run(host="0.0.0.0", port=5000, debug=True)
