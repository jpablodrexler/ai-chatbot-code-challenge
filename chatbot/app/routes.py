from flask import Blueprint, jsonify, request, render_template_string, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
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
from app.models import User
from app.user_store import list_users, add_user, get_user, hash_password

secret_key = 'SecretKey'
orders_bp = Blueprint('orders', __name__)

load_dotenv()

model = os.environ.get('MODEL')
model_temperature = os.environ.get('MODEL_TEMPERATURE')

print(model)
print(model_temperature)

response_model = init_chat_model(model, temperature=model_temperature)

# Health check
@orders_bp.route('/health', methods=['GET'])
def get_health():
    return "OK", 200

# Register user endpoint
@orders_bp.route('/users/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    users = list_users()
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if username in users:
        return jsonify({'error': 'Username already exists'}), 409
    add_user(username, hash_password(password))
    return jsonify({'message': 'User registered successfully'}), 201

# Login validation endpoint
@orders_bp.route('/users/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    users = list_users()
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    user = get_user(username)

    if user['password'] != hash_password(password):
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

    response = send_promt_to_model(prompt)
    
    # Return a chat response
    return jsonify({'response': response}), 200

def send_promt_to_model(prompt):
    # Asking a question to the model without using the knowledge database.
    response = response_model.invoke(prompt).content
    # TODO: Could use env variable to mock?
    #response = 'response from the bot'
    
    # Return a chat response
    return response

# Store messages in memory
# TODO: Should depend on the user
chat_history = []

# HTML template for the chat interface
chat_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Interface</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .chat-container { width: 400px; margin: 50px auto; background-color: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .message { padding: 10px; margin: 5px 0; border-radius: 10px; max-width: 80%; }
        .user { background-color: #dcf8c6; text-align: right; }
        .bot { background-color: #ececec; text-align: left; }
        .chat-box { display: flex; flex-direction: column; }
        .input-container { display: flex; margin-top: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        button { padding: 10px; border: none; background-color: #4CAF50; color: white; border-radius: 5px; margin-left: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Chat</h2>
        <div class="chat-box">
            {% for msg in messages %}
                <div class="message {{ msg['sender'] }}">{{ msg['text'] }}</div>
            {% endfor %}
        </div>
        <form method="post" action="{{ url_for('orders.chatui') }}">
            <div class="input-container">
                <input type="text" name="message" placeholder="Type your message..." required>
                <button type="submit">Send</button>
            </div>
        </form>
    </div>
</body>
</html>
"""

@orders_bp.route('/chatui', methods=['GET', 'POST'])
@login_required
def chatui():
    if request.method == 'POST':
        user_message = request.form['message']
        chat_history.append({'sender': 'user', 'text': user_message})

        bot_response = send_promt_to_model(user_message)

        chat_history.append({'sender': 'bot', 'text': bot_response})
        return redirect(url_for('orders.chatui'))
    return render_template_string(chat_template, messages=chat_history)

# HTML template for the login interface
login_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .login-container { width: 400px; margin: 50px auto; background-color: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .input-container { display: flex; flex-direction: column; margin-top: 10px; }
        input[type="text"] { flex: 1; margin: 10px; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        input[type="password"] { flex: 1; margin: 10px; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        button { margin: 10px; padding: 10px; border: none; background-color: #4CAF50; color: white; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Login</h2>
        <form method="post">
            <div class="input-container">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </div>
        </form>
    </div>
</body>
</html>
"""

@orders_bp.route('/loginui', methods=['GET', 'POST'])
def loginui():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get(username)
        users = list_users()
        if user and users[username]['password'] == hash_password(password):
            login_user(user)
            return redirect(url_for('orders.chatui'))
        flash('Invalid credentials')
    return render_template_string(login_template)

@orders_bp.route('/logoutui')
@login_required
def logoutui():
    logout_user()
    return redirect(url_for('orders.loginui'))
