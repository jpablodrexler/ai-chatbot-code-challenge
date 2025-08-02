from flask_login import UserMixin
from app.user_store import list_users

class User(UserMixin):
    def __init__(self, username):
        self.id = username

    @staticmethod
    def get(username):
        users = list_users()
        if username in users:
            return User(username)
        return None
