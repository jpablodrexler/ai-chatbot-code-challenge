from threading import Lock

# Helper function to hash passwords
import hashlib
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

users = {
    "admin": {"password": hash_password("admin123"), "role": "admin"}
}

# Lock for thread-safe access
user_lock = Lock()

def get_user(username):
    with user_lock:
        return users.get(username)

def add_user(username, password, role="user"):
    with user_lock:
        users[username] = {"password": password, "role": role}

def list_users():
    with user_lock:
        return dict(users)  # Return a copy to avoid race conditions
