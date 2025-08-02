from flask import Flask
from app.routes import orders_bp
from flask_login import LoginManager
from app.models import User

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.register_blueprint(orders_bp)
    app.secret_key = 'SecretKey'
    login_manager.init_app(app)
    login_manager.login_view = 'orders.loginui'
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
