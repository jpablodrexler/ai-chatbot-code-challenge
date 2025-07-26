from flask import Blueprint, jsonify, request
import jwt
from datetime import datetime, timedelta

secret_key = 'SecretKey'
orders_bp = Blueprint('orders', __name__)

# Sample order endpoint
@orders_bp.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    return jsonify({
        'order_id': id,
        'details': {
            'item': 'Laptop',
            'quantity': 1
        }
    })

# In-memory user store
users = {}

# Helper function to hash passwords
import hashlib
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register user endpoint
@orders_bp.route('/users/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if username in users:
        return jsonify({'error': 'Username already exists'}), 409
    users[username] = hash_password(password)
    return jsonify({'message': 'User registered successfully'}), 201

# Login validation endpoint
@orders_bp.route('/users/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    if users[username] != hash_password(password):
        return jsonify({'error': 'Invalid password'}), 401

    # Generate JWT token
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Token expiration time
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')

    # Return JWT token in the response
    return jsonify({
        'message': 'Login successful',
        'token': token
    }), 200
