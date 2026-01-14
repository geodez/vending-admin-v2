"""
Unit tests for authentication.
"""
import pytest
import time
import hashlib
import hmac
from app.auth.jwt import create_access_token, decode_access_token
from app.auth.telegram import validate_telegram_login_widget
from app.config import settings


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


def test_validate_telegram_login_widget_valid():
    """Test Telegram Login Widget validation with valid signature."""
    bot_token = "test_token_123"
    auth_date = int(time.time())
    
    # Создаем валидные данные
    auth_data = {
        "id": 602720033,
        "first_name": "Test",
        "username": "testuser",
        "auth_date": auth_date,
    }
    
    # Вычисляем правильный hash (как в реальном алгоритме Login Widget)
    check_items = []
    for key in sorted(auth_data.keys()):
        value = auth_data[key]
        if value is not None:
            check_items.append(f"{key}={value}")
    
    check_string = "\n".join(check_items)  # ВАЖНО: реальный \n, не \\n
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    
    auth_data["hash"] = calculated_hash
    
    # Проверяем валидацию
    assert validate_telegram_login_widget(auth_data, bot_token) is True


def test_validate_telegram_login_widget_invalid_hash():
    """Test Telegram Login Widget validation with invalid signature."""
    bot_token = "test_token_123"
    auth_date = int(time.time())
    
    auth_data = {
        "id": 602720033,
        "first_name": "Test",
        "auth_date": auth_date,
        "hash": "invalid_hash_123456",
    }
    
    # Проверяем валидацию (должна провалиться)
    assert validate_telegram_login_widget(auth_data, bot_token) is False


def test_validate_telegram_login_widget_missing_hash():
    """Test Telegram Login Widget validation with missing hash."""
    bot_token = "test_token_123"
    auth_date = int(time.time())
    
    auth_data = {
        "id": 602720033,
        "first_name": "Test",
        "auth_date": auth_date,
    }
    
    # Проверяем валидацию (должна провалиться - нет hash)
    assert validate_telegram_login_widget(auth_data, bot_token) is False
