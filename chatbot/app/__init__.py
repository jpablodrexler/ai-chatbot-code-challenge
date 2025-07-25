from flask import Flask
from app.routes import orders_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(orders_bp)
    return app
