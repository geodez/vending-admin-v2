"""
Tests for Telegram OAuth authentication and RBAC.
"""
import pytest
import json
import hashlib
import hmac
import time
from app.auth.jwt import verify_token
from app.config import settings


def generate_telegram_oauth_hash(data: dict, bot_token: str) -> str:
    """
    Generate valid Telegram OAuth hash for testing.
    
    Args:
        data: User data dict (id, first_name, auth_date, etc.)
        bot_token: Bot token for hash calculation
    
    Returns:
        Valid hash string
    """
    # Create data_check_string by sorting keys
    data_to_check = {k: v for k, v in data.items() if k != 'hash'}
    data_check_arr = [f"{k}={v}" for k, v in sorted(data_to_check.items())]
    data_check_string = '\n'.join(data_check_arr)
    
    # Calculate HMAC SHA256
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


class TestTelegramOAuth:
    """Test Telegram OAuth endpoint."""
    
    def test_oauth_valid_user(self, client, db_session, create_test_user):
        """
        Test successful login with valid Telegram hash and existing user.
        
        Acceptance:
        - Valid hash + user exists → 200 + JWT
        """
        # Create test user
        user = create_test_user(
            telegram_user_id=123456,
            role="operator",
            is_active=True
        )
        
        # Create valid OAuth data
        oauth_data = {
            "id": 123456,
            "first_name": "Test",
            "username": "testuser",
            "auth_date": int(time.time()),
        }
        
        # Generate valid hash
        oauth_data["hash"] = generate_telegram_oauth_hash(
            oauth_data, 
            settings.TELEGRAM_BOT_TOKEN
        )
        
        # Send request
        response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        # Validate response
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == user.id
        assert data["user"]["telegram_user_id"] == 123456
        assert data["user"]["role"] == "operator"
        
        # Validate JWT token
        payload = verify_token(data["access_token"])
        assert payload is not None
        assert payload["user_id"] == user.id
        assert payload["role"] == "operator"
    
    def test_oauth_invalid_hash(self, client):
        """
        Test login fails with invalid hash.
        
        Acceptance:
        - Invalid hash → 401 Unauthorized
        """
        oauth_data = {
            "id": 123456,
            "first_name": "Test",
            "auth_date": int(time.time()),
            "hash": "invalid_hash_value"
        }
        
        response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Доступ запрещен"
    
    def test_oauth_user_not_found(self, client):
        """
        Test login fails when user doesn't exist in DB.
        
        Acceptance:
        - Valid hash, user absent → 403 "Доступ запрещен"
        """
        # Create valid OAuth data for non-existent user
        oauth_data = {
            "id": 999999,
            "first_name": "Unknown",
            "username": "unknown",
            "auth_date": int(time.time()),
        }
        
        # Generate valid hash
        oauth_data["hash"] = generate_telegram_oauth_hash(
            oauth_data,
            settings.TELEGRAM_BOT_TOKEN
        )
        
        response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Доступ запрещен"
    
    def test_oauth_inactive_user(self, client, create_test_user):
        """
        Test login fails when user is inactive.
        
        Acceptance:
        - Valid hash, user inactive → 403 "Доступ запрещен"
        """
        # Create inactive user
        user = create_test_user(
            telegram_user_id=123456,
            role="operator",
            is_active=False
        )
        
        # Create valid OAuth data
        oauth_data = {
            "id": 123456,
            "first_name": "Test",
            "auth_date": int(time.time()),
        }
        
        # Generate valid hash
        oauth_data["hash"] = generate_telegram_oauth_hash(
            oauth_data,
            settings.TELEGRAM_BOT_TOKEN
        )
        
        response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Доступ запрещен"
    
    def test_oauth_expired_auth_date(self, client, create_test_user):
        """
        Test login fails when auth_date is too old (> 24 hours).
        
        Acceptance:
        - Valid hash, auth_date > 24h old → 401 Unauthorized
        """
        # Create test user
        user = create_test_user(
            telegram_user_id=123456,
            role="operator",
            is_active=True
        )
        
        # Create OAuth data with old auth_date (> 24 hours)
        oauth_data = {
            "id": 123456,
            "first_name": "Test",
            "auth_date": int(time.time()) - (25 * 3600),  # 25 hours ago
        }
        
        # Generate valid hash
        oauth_data["hash"] = generate_telegram_oauth_hash(
            oauth_data,
            settings.TELEGRAM_BOT_TOKEN
        )
        
        response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Доступ запрещен"


class TestRBAC:
    """Test Role-Based Access Control."""
    
    def test_owner_can_access_owner_report(self, client, create_test_user):
        """
        Test owner can access owner-only endpoint.
        
        Acceptance:
        - owner JWT → /owner-report = 200
        """
        # Create owner user
        owner = create_test_user(
            telegram_user_id=111111,
            role="owner",
            is_active=True
        )
        
        # Get JWT token for owner
        oauth_data = {
            "id": 111111,
            "first_name": "Owner",
            "auth_date": int(time.time()),
        }
        oauth_data["hash"] = generate_telegram_oauth_hash(
            oauth_data,
            settings.TELEGRAM_BOT_TOKEN
        )
        
        login_response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Try to access owner-only endpoint
        headers = {"Authorization": f"Bearer {token}"}
        report_response = client.get(
            "/api/v1/analytics/owner-report",
            headers=headers
        )
        
        # Owner should have access
        assert report_response.status_code == 200
    
    def test_operator_cannot_access_owner_report(self, client, create_test_user):
        """
        Test operator cannot access owner-only endpoint.
        
        Acceptance:
        - operator JWT → /owner-report = 403
        """
        # Create operator user
        operator = create_test_user(
            telegram_user_id=222222,
            role="operator",
            is_active=True
        )
        
        # Get JWT token for operator
        oauth_data = {
            "id": 222222,
            "first_name": "Operator",
            "auth_date": int(time.time()),
        }
        oauth_data["hash"] = generate_telegram_oauth_hash(
            oauth_data,
            settings.TELEGRAM_BOT_TOKEN
        )
        
        login_response = client.post(
            "/api/v1/auth/telegram_oauth",
            json={"init_data": json.dumps(oauth_data)}
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Try to access owner-only endpoint
        headers = {"Authorization": f"Bearer {token}"}
        report_response = client.get(
            "/api/v1/analytics/owner-report",
            headers=headers
        )
        
        # Operator should NOT have access
        assert report_response.status_code == 403
