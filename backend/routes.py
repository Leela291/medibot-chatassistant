# backend/routes.py
from flask import Flask
from backend.chatbot_api import chatbot_bp, health_bp, admin_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(chatbot_bp, url_prefix="/api")
    app.register_blueprint(admin_bp,   url_prefix="/api/admin")
