import pytest
from app import create_app

app = create_app()

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

def test_register_route(client):
    response = client.post('/users/register', json={'username': 'alice', 'password': 'password123'})
    assert response.status_code == 201

def test_register_duplicate_user(client):
    response = client.post('/users/register', json={'username': 'jill', 'password': 'password345'})
    assert response.status_code == 201
    assert 'message' in response.json

    response = client.post('/users/register', json={'username': 'jill', 'password': 'password123'})
    assert response.status_code == 409
    assert 'error' in response.json

def test_login_route(client):
    response = client.post('/users/login', json={'username': 'alice', 'password': 'password123'})
    assert response.status_code == 200

def test_invalid_login(client):
    response = client.post('/users/login', json={'username': 'alice', 'password': 'password456'})
    assert response.status_code == 401
    assert 'error' in response.json

def test_chat_route_unauthorized(client):
    response = client.post('/chat', json={'prompt': 'Hello, world!'})
    assert response.status_code == 401
    assert 'error' in response.json

# TODO: Mock the LLM
# def test_chat_authorized(client):
#     # Login to get a token
#     response = client.post('/users/login', json={'username': 'alice', 'password': 'password123'})
#     token = response.json['token']
    
#     # Set the header with the token
#     headers = {'Authorization': f'Bearer {token}'}

#     # Send the request with the header
#     response = client.post('/chat', json={'prompt': 'Hello, world!'}, headers=headers)
#     # Assert the response status code and content
#     assert response.status_code == 200
#     assert 'response' in response.json
