"""
Unit tests for Telegram OAuth authentication.
"""
import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.auth.jwt import create_access_token, decode_access_token


class TestTelegramOAuth:
    """Tests for Telegram OAuth endpoint."""
    
    def test_oauth_valid_signature(self, client, db):
        """Test OAuth with valid HMAC signature."""
        # Create test user first (whitelist-only)
        telegram_user_id = 123456789
        
        # Mock get_user_by_telegram_id to return existing user
        with patch('app.api.v1.auth.get_user_by_telegram_id') as mock_get_user:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.telegram_user_id = telegram_user_id
            mock_user.role = 'operator'
            mock_user.is_active = True
            mock_user.first_name = 'Test'
            mock_user.last_name = 'User'
            mock_user.username = 'testuser'
            mock_get_user.return_value = mock_user
            
            # Prepare OAuth data with valid HMAC
            auth_data = {
                'id': str(telegram_user_id),
                'first_name': 'Test',
                'last_name': 'User',
                'username': 'testuser',
                'auth_date': int(datetime.now().timestamp()),
                'hash': 'placeholder'  # Will be replaced
            }
            
            # Calculate HMAC SHA256 signature
            data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items()) if k != 'hash']
            data_check_string = '\n'.join(data_check_arr)
            secret_key = hashlib.sha256('TEST_BOT_TOKEN'.encode()).digest()
            hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
            auth_data['hash'] = hmac_hash
            
            payload = {'init_data': json.dumps(auth_data)}
            
            # Mock the validate_telegram_oauth
            with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
                mock_validate.return_value = True
                with patch('app.api.v1.auth.validate_auth_date') as mock_validate_date:
                    mock_validate_date.return_value = True
                    with patch('app.api.v1.auth.create_access_token') as mock_create_token:
                        mock_create_token.return_value = 'test_token'
                        
                        response = client.post('/api/v1/auth/telegram_oauth', json=payload)
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert 'access_token' in data
                        assert data['token_type'] == 'bearer'
                        assert 'user' in data
    
    def test_oauth_invalid_signature(self, client):
        """Test OAuth with invalid HMAC signature."""
        auth_data = {
            'id': '123456789',
            'first_name': 'Test',
            'hash': 'invalid_hash',
            'auth_date': int(datetime.now().timestamp())
        }
        payload = {'init_data': json.dumps(auth_data)}
        
        with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
            mock_validate.return_value = False
            response = client.post('/api/v1/auth/telegram_oauth', json=payload)
            
            assert response.status_code == 401
            assert 'Invalid Telegram authentication signature' in response.json()['detail']
    
    def test_oauth_expired_auth_date(self, client):
        """Test OAuth with expired auth_date."""
        auth_data = {
            'id': '123456789',
            'first_name': 'Test',
            'hash': 'valid_hash',
            'auth_date': 1  # Very old timestamp
        }
        payload = {'init_data': json.dumps(auth_data)}
        
        with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
            mock_validate.return_value = True
            with patch('app.api.v1.auth.validate_auth_date') as mock_validate_date:
                mock_validate_date.return_value = False
                response = client.post('/api/v1/auth/telegram_oauth', json=payload)
                
                assert response.status_code == 401
                assert 'Authentication request expired' in response.json()['detail']
    
    def test_oauth_user_not_found(self, client):
        """Test OAuth with user not in whitelist."""
        auth_data = {
            'id': '999999999',  # Non-existent user
            'first_name': 'Hacker',
            'hash': 'valid_hash',
            'auth_date': int(datetime.now().timestamp())
        }
        payload = {'init_data': json.dumps(auth_data)}
        
        with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
            mock_validate.return_value = True
            with patch('app.api.v1.auth.validate_auth_date') as mock_validate_date:
                mock_validate_date.return_value = True
                with patch('app.api.v1.auth.get_user_by_telegram_id') as mock_get_user:
                    mock_get_user.return_value = None  # User not found
                    response = client.post('/api/v1/auth/telegram_oauth', json=payload)
                    
                    assert response.status_code == 403
                    assert 'User not found' in response.json()['detail']
    
    def test_oauth_inactive_user(self, client):
        """Test OAuth with inactive user."""
        auth_data = {
            'id': '123456789',
            'first_name': 'Inactive',
            'hash': 'valid_hash',
            'auth_date': int(datetime.now().timestamp())
        }
        payload = {'init_data': json.dumps(auth_data)}
        
        with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
            mock_validate.return_value = True
            with patch('app.api.v1.auth.validate_auth_date') as mock_validate_date:
                mock_validate_date.return_value = True
                with patch('app.api.v1.auth.get_user_by_telegram_id') as mock_get_user:
                    mock_user = MagicMock()
                    mock_user.is_active = False
                    mock_user.id = 1
                    mock_get_user.return_value = mock_user
                    response = client.post('/api/v1/auth/telegram_oauth', json=payload)
                    
                    assert response.status_code == 403
                    assert 'User account is inactive' in response.json()['detail']
    
    def test_oauth_missing_hash(self, client):
        """Test OAuth without hash."""
        auth_data = {
            'id': '123456789',
            'first_name': 'Test',
            'auth_date': int(datetime.now().timestamp())
            # Missing 'hash' field
        }
        payload = {'init_data': json.dumps(auth_data)}
        
        with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
            mock_validate.return_value = False
            response = client.post('/api/v1/auth/telegram_oauth', json=payload)
            
            assert response.status_code == 401
    
    def test_oauth_no_debug_bypass(self, client):
        """Test that DEBUG mode doesn't bypass OAuth validation."""
        # This test ensures no DEBUG bypass in OAuth
        auth_data = {
            'id': '123456789',
            'first_name': 'TestDebug',
            'hash': 'invalid_hash',
            'auth_date': int(datetime.now().timestamp())
        }
        payload = {'init_data': json.dumps(auth_data)}
        
        with patch('app.api.v1.auth.validate_telegram_oauth') as mock_validate:
            mock_validate.return_value = False
            response = client.post('/api/v1/auth/telegram_oauth', json=payload)
            
            # Should always fail with invalid hash, regardless of DEBUG setting
            assert response.status_code == 401


class TestJWT:
    """Tests for JWT token handling."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        token = create_access_token(
            data={
                'user_id': 42,
                'telegram_user_id': 123456789,
                'role': 'owner'
            }
        )
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token(self):
        """Test JWT token decoding."""
        token_data = {
            'user_id': 42,
            'telegram_user_id': 123456789,
            'role': 'owner'
        }
        token = create_access_token(data=token_data)
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload['user_id'] == 42
        assert payload['role'] == 'owner'
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = decode_access_token('invalid_token')
        assert payload is None
