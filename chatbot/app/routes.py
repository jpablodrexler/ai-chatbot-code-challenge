import os
import openai
import requests
import json
from flask import Blueprint, request, jsonify, render_template_string, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import jwt
from datetime import datetime, timedelta
from app.models import User
from app.user_store import list_users, add_user, get_user, hash_password
import time

secret_key = 'SecretKey'
orders_bp = Blueprint('orders', __name__)

openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"

def send_promt_to_model(prompt):
    # Azure OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_DEPLOYMENT"):
        try:
            client = openai.AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2023-05-15",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            for attempt in range(2):  # 1 reintento en caso de rate limit
                try:
                    response = client.chat.completions.create(
                        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                        messages=[
                            {"role": "system", "content": "Eres un asistente cordial y amable para e-commerce."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=256,
                        temperature=float(os.getenv("MODEL_TEMPERATURE", 0.7))
                    )
                    return response.choices[0].message.content
                except openai.RateLimitError:
                    if attempt == 0:
                        time.sleep(2)
                        continue
                    else:
                        return "El servicio está ocupado. Por favor, intenta nuevamente en unos segundos."
        except openai.AuthenticationError:
            return "Error de autenticación con Azure OpenAI. Verifica tu API Key."
        except openai.APIConnectionError:
            return "No se pudo conectar a Azure OpenAI. Intenta más tarde."
        except Exception as e:
            return f"Ocurrió un error inesperado: {str(e)}"
    # Ollama local
    elif os.getenv("MODEL") and os.getenv("MODEL").startswith("ollama:"):
        try:
            ollama_model = os.getenv("MODEL").replace("ollama:", "")
            ollama_url = "http://localhost:11434/api/generate"
            payload = {
                "model": ollama_model,
                "prompt": prompt,
                "temperature": float(os.getenv("MODEL_TEMPERATURE", 0.7))
            }
            for attempt in range(2):  # 1 reintento en caso de rate limit
                response = requests.post(ollama_url, json=payload)
                if response.status_code == 429:
                    if attempt == 0:
                        time.sleep(2)
                        continue
                    else:
                        return "El modelo local está ocupado. Intenta nuevamente en unos segundos."
                elif response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    full_response = ""
                    for line in lines:
                        try:
                            result = json.loads(line)
                            if "response" in result and result["response"].strip():
                                full_response += result["response"]
                        except Exception:
                            continue
                    if full_response:
                        return full_response
                    return "Error: No se pudo procesar la respuesta del modelo local."
                else:
                    return f"Error: {response.text}"
        except requests.ConnectionError:
            return "No se pudo conectar al modelo local. Asegúrate de que Ollama esté corriendo."
        except Exception as e:
            return f"Ocurrió un error inesperado: {str(e)}"
    else:
        return "Error: No hay configuración válida de modelo en .env"

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
