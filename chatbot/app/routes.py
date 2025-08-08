from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
import openai
import requests
import json
from flask import Blueprint, request, jsonify, render_template_string, redirect, url_for, flash, session
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

def get_vector_search_context_sdk(prompt_embedding, top_k=3):
    """
    Query Azure AI Search vector resource using azure-search-documents SDK and return relevant context chunks.
    """
    SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')
    SEARCH_API_KEY = os.getenv('AZURE_SEARCH_ADMIN_KEY')
    SEARCH_INDEX = os.getenv('AZURE_SEARCH_INDEX', 'documents')
    try:
        client = SearchClient(
            endpoint=SEARCH_ENDPOINT,
            index_name=SEARCH_INDEX,
            credential=AzureKeyCredential(SEARCH_API_KEY)
        )
        results = client.search(
            search_text=prompt_embedding,  # Empty for pure vector search
            # vector=prompt_embedding,
            # vector_fields="embedding",
            top=top_k,
            select=["content"]
        )
        context_chunks = [doc["content"] for doc in results if "content" in doc]
        print(f"SDK context chunks found: {len(context_chunks)}")
        if context_chunks:
            return "\n---\n".join(context_chunks)
    except Exception as e:
        print(f"SDK Error retrieving context: {str(e)}")
    return ""

def send_prompt_to_model(prompt):
    print(f"Received prompt: {prompt}")  # Log the prompt for debugging

    # Retrieve or initialize message history from session
    history = session.get('message_history', [])

    context = get_vector_search_context_sdk(prompt)
    print(f"Context retrieved: {context[:100]}...")  # Log first 100 chars of context for debugging

    # Compose messages for model (system + history + context + new prompt)
    messages = [{"role": "system", "content": "Eres un asistente cordial y amable para e-commerce."}]
    for msg in history:
        messages.append({"role": msg['sender'], "content": msg['text']})
    if context:
        messages.append({"role": "system", "content": f"Contexto relevante:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    print(f"Messages prepared for model: {messages}")

    response_text = None
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
                        messages=messages,
                        max_tokens=256,
                        temperature=float(os.getenv("MODEL_TEMPERATURE", 0.7))
                    )
                    response_text = response.choices[0].message.content
                    break
                except openai.RateLimitError:
                    if attempt == 0:
                        time.sleep(2)
                        continue
                    else:
                        response_text = "El servicio está ocupado. Por favor, intenta nuevamente en unos segundos."
                        break
        except openai.AuthenticationError:
            response_text = "Error de autenticación con Azure OpenAI. Verifica tu API Key."
        except openai.APIConnectionError:
            response_text = "No se pudo conectar a Azure OpenAI. Intenta más tarde."
        except Exception as e:
            response_text = f"Ocurrió un error inesperado: {str(e)}"
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
                        response_text = "El modelo local está ocupado. Intenta nuevamente en unos segundos."
                        break
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
                        response_text = full_response
                    else:
                        response_text = "Error: No se pudo procesar la respuesta del modelo local."
                    break
                else:
                    response_text = f"Error: {response.text}"
                    break
        except requests.ConnectionError:
            response_text = "No se pudo conectar al modelo local. Asegúrate de que Ollama esté corriendo."
        except Exception as e:
            response_text = f"Ocurrió un error inesperado: {str(e)}"
    else:
        response_text = "Error: No hay configuración válida de modelo en .env"

    # Update session history
    history.append({'sender': 'user', 'text': prompt})
    history.append({'sender': 'assistant', 'text': response_text})
    session['message_history'] = history
    return response_text

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

    # Initialize session for user
    session['username'] = username
    session['message_history'] = []

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
        # Set session username if not already set
        if 'username' not in session:
            session['username'] = payload.get('username')
            session['message_history'] = []
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json()
    prompt = data.get('prompt')

    response = send_prompt_to_model(prompt)

    # Return a chat response
    return jsonify({'response': response}), 200

## Store messages in session per user (handled in send_promt_to_model)

# HTML template for the chat interface
chat_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Chat Interface</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
        .chat-container { width: 400px; margin: 50px auto; background-color: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); position: relative; }
        .message { padding: 10px; margin: 5px 0; border-radius: 10px; max-width: 80%; }
        .user { background-color: #dcf8c6; text-align: right; }
        .bot { background-color: #ececec; text-align: left; }
        .chat-box { display: flex; flex-direction: column; }
        .input-container { display: flex; margin-top: 10px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        button { padding: 10px; border: none; background-color: #4CAF50; color: white; border-radius: 5px; margin-left: 5px; cursor: pointer; }
        .logout-btn {
            background-color: #f44336;
            position: fixed;
            right: 30px;
            top: 30px;
            z-index: 1000;
            border-radius: 50px;
            padding: 12px 24px;
            font-size: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Keystorm Chat</h2>
        <h3>Keyboards seller</h3>
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
    <form method="get" action="{{ url_for('orders.logoutui') }}">
        <button type="submit" class="logout-btn">Logout</button>
    </form>
</body>
</html>
"""

@orders_bp.route('/chatui', methods=['GET', 'POST'])
@login_required
def chatui():
    if 'message_history' not in session:
        session['message_history'] = []
    if request.method == 'POST':
        user_message = request.form['message']
        # send_promt_to_model will update session['message_history']
        send_prompt_to_model(user_message)
        return redirect(url_for('orders.chatui'))
    # Filter only user/assistant for UI
    ui_history = [msg for msg in session.get('message_history', []) if msg['sender'] in ['user', 'assistant']]
    # For UI, map 'assistant' to 'bot'
    for msg in ui_history:
        if msg['sender'] == 'assistant':
            msg['sender'] = 'bot'
    return render_template_string(chat_template, messages=ui_history)


# Endpoint to reset Azure AI Search data from keystorm_vector_chunks.json
@orders_bp.route('/reset-data', methods=['POST'])
def reset_data():
    """
    Clears the Azure AI Search index and uploads new data from keystorm_vector_chunks.json.
    """
    import requests
    import uuid
    # Config: set these to your Azure AI Search details
    SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')  # e.g. https://<your-search>.search.windows.net
    SEARCH_API_KEY = os.getenv('AZURE_SEARCH_ADMIN_KEY')  # Admin key
    SEARCH_INDEX = os.getenv('AZURE_SEARCH_INDEX', 'documents')

    if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
        return jsonify({'error': 'Azure Search endpoint or key not configured'}), 500

    headers = {
        'Content-Type': 'application/json',
        'api-key': SEARCH_API_KEY
    }

    # 1. Delete all documents in the index
    # Get all document keys (assume 'id' is key)
    list_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/search?api-version=2023-11-01"
    list_body = {"search": "*", "select": "id", "top": 1000}
    r = requests.post(list_url, headers=headers, json=list_body)
    if r.status_code != 200:
        return jsonify({'error': 'Failed to list documents', 'details': r.text}), 500
    ids = [doc['id'] for doc in r.json().get('value', [])]
    if ids:
        # Delete by batch
        delete_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/index?api-version=2023-11-01"
        delete_body = {"value": [{"@search.action": "delete", "id": id} for id in ids]}
        r = requests.post(delete_url, headers=headers, json=delete_body)
        if r.status_code not in [200, 201]:
            return jsonify({'error': 'Failed to delete documents', 'details': r.text}), 500

    # 2. Read new data from keystorm_vector_chunks.json
    try:
        with open('keystorm_vector_chunks.json', 'r', encoding='utf-8') as f:
            chunks = json.load(f)
    except Exception as e:
        return jsonify({'error': 'Failed to read keystorm_vector_chunks.json', 'details': str(e)}), 500

    # 3. Upload new documents
    # Each chunk should have: id, content, embedding
    upload_url = f"{SEARCH_ENDPOINT}/indexes/{SEARCH_INDEX}/docs/index?api-version=2023-11-01"
    docs = []
    for chunk in chunks:
        doc = {
            "id": chunk.get('id', str(uuid.uuid4())),
            "content": chunk.get('content', ''),
            "embedding": chunk.get('embedding', [])
        }
        docs.append(doc)
    upload_body = {"value": [{"@search.action": "upload", **doc} for doc in docs]}
    r = requests.post(upload_url, headers=headers, json=upload_body)
    if r.status_code not in [200, 201]:
        return jsonify({'error': 'Failed to upload documents', 'details': r.text}), 500

    return jsonify({'message': f'Reset complete. Uploaded {len(docs)} documents.'}), 200

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
    # Clear chat history from session
    session.pop('message_history', None)
    session.pop('username', None)
    return redirect(url_for('orders.loginui'))
