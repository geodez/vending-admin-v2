"""
Unit tests for authentication.
"""
import pytest
from app.auth.jwt import create_access_token, decode_access_token


def test_create_access_token():
    """Test JWT token creation."""
    user_id = 1
    token = create_access_token(user_id=user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token():
    """Test JWT token decoding."""
    user_id = 42
    token = create_access_token(user_id=user_id)
    payload = decode_access_token(token)
    assert payload["user_id"] == user_id


def test_decode_invalid_token():
    """Test decoding invalid token."""
    payload = decode_access_token("invalid_token")
    assert payload is None


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
