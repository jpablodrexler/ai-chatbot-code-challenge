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

def test_login_route(client):
    response = client.post('/users/login', json={'username': 'alice', 'password': 'password123'})
    assert response.status_code == 200

def test_chat_route_unauthorized(client):
    response = client.post('/chat', json={'prompt': 'Hello, world!'})
    assert response.status_code == 401
    assert 'error' in response.json
