from flask import Blueprint, jsonify, request
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model

secret_key = 'SecretKey'
orders_bp = Blueprint('orders', __name__)

load_dotenv()

model = os.environ.get('MODEL')
model_temperature = os.environ.get('MODEL_TEMPERATURE')

print('MODEL: ' + model)
print('MODEL_TEMPERATURE: ' + model_temperature)

response_model = init_chat_model(model, temperature=model_temperature)

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

# Chat endpoint
@orders_bp.route('/chat', methods=['POST'])
def chat():
    # Check if the user is authenticated
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    # Decode the JWT token
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.get_json()
    prompt = data.get('prompt')

    # Asking a question to the model without using the knowledge database.
    response = response_model.invoke(prompt).content
    
    # Return a chat response
    return jsonify({'response': response}), 200
