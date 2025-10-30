"""Tests for the main Flask application."""

import pytest
import json
from src.app import create_app
from src.models import Product, ProductCategory


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'smartshopper-ai'
    assert 'dependencies' in data


def test_api_info_endpoint(client):
    """Test API info endpoint."""
    response = client.get('/api')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['message'] == 'Welcome to SmartShopper AI API'
    assert data['version'] == '1.0.0'


def test_search_endpoint_no_data(client):
    """Test search endpoint with no data."""
    response = client.post('/api/search')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data


def test_search_endpoint_invalid_data(client):
    """Test search endpoint with invalid data."""
    response = client.post('/api/search', 
                          json={'invalid_field': 'test'})
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data


def test_search_endpoint_valid_data(client):
    """Test search endpoint with valid data."""
    search_data = {
        'query': 'test product',
        'page': 1,
        'page_size': 10
    }
    
    response = client.post('/api/search',
                          headers={'Content-Type': 'application/json'},
                          json=search_data)
    
    # Should succeed (might return empty results if no data indexed)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'query' in data
    assert 'products' in data
    assert 'total' in data


def test_chat_endpoint_no_data(client):
    """Test chat endpoint with no data."""
    response = client.post('/api/chat')
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert 'error' in data


def test_chat_endpoint_valid_data(client):
    """Test chat endpoint with valid data."""
    chat_data = {
        'message': 'Hello, I need help finding a laptop'
    }
    
    response = client.post('/api/chat',
                          headers={'Content-Type': 'application/json'},
                          json=chat_data)
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'response' in data
    assert 'products' in data
    assert 'suggestions' in data


def test_home_endpoint(client):
    """Test home endpoint returns HTML."""
    response = client.get('/')
    assert response.status_code == 200
    # Should serve the HTML file
    assert b'SmartShopper AI' in response.data


def test_404_handler(client):
    """Test 404 error handler."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['error'] == 'Endpoint not found'