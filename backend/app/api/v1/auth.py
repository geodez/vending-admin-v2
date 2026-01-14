from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.auth.telegram import validate_telegram_init_data
from app.auth.jwt import create_access_token
from app.crud.user import get_user_by_telegram_id
from app.schemas.auth import TelegramAuthRequest, TokenResponse, UserResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.config import settings
import hmac
import hashlib
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_telegram_oauth(data: dict, bot_token: str) -> bool:
    '''
    Проверка подписи Telegram OAuth (https://core.telegram.org/widgets/login#checking-authorization)
    Validates HMAC SHA256 signature of the OAuth data.
    
    Security: No DEBUG bypass. Always validates signature.
    '''
    auth_data = data.copy()
    hash_ = auth_data.pop('hash', None)
    if not hash_:
        return False
    
    data_check_arr = [f"{k}={v}" for k, v in sorted(auth_data.items())]
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac_hash == hash_


def validate_auth_date(auth_date: int, max_age_seconds: int = 86400) -> bool:
    '''
    Проверка, что auth_date не старше максимально допустимого времени (по умолчанию 24 часа).
    Защита от reply-attack.
    '''
    import time
    current_time = int(time.time())
    return (current_time - auth_date) <= max_age_seconds


@router.post("/telegram_oauth", response_model=TokenResponse)
def authenticate_telegram_oauth_post(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Telegram OAuth endpoint (POST from frontend).
    
    Security baseline:
    - STRICT: No DEBUG bypass or hardcoded IDs
    - Hash HMAC-SHA256 validation (REQUIRED)
    - auth_date check (24h max age)
    - Whitelist-only: User must exist in DB (no auto-create)
    - Returns 401 for invalid auth, 403 for user not found/inactive
    """
    try:
        # Parse JSON init_data from Telegram widget
        user_data = json.loads(request.init_data)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse init_data JSON")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OAuth data format"
        )
    
    # P0: Validate HMAC signature (ALWAYS, no DEBUG bypass)
    if not validate_telegram_oauth(user_data, settings.TELEGRAM_BOT_TOKEN):
        logger.warning(f"Invalid Telegram signature for user_id={user_data.get('id')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication signature"
        )
    
    # P0: Validate auth_date is recent (ALWAYS, no DEBUG bypass)
    auth_date = user_data.get('auth_date')
    if not auth_date or not validate_auth_date(auth_date):
        logger.warning(f"Invalid auth_date for user_id={user_data.get('id')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication request expired"
        )
    
    telegram_user_id = user_data.get('id')
    if not telegram_user_id:
        logger.warning("Missing telegram user id in OAuth data")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data"
        )
    
    # P0: Whitelist-only - user MUST exist in DB (no auto-create)
    user = get_user_by_telegram_id(db, telegram_user_id)
    if not user:
        logger.info(f"OAuth attempt for non-whitelisted user {telegram_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found in system"
        )
    
    # Check if user account is active
    if not user.is_active:
        logger.warning(f"OAuth attempt for inactive user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate JWT token
    token = create_access_token(
        data={
            "user_id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "role": user.role
        }
    )
    
    logger.info(f"Successful OAuth for user {user.id} (telegram_id={telegram_user_id})")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/telegram", response_model=TokenResponse)
def authenticate_telegram(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Telegram Mini App authentication endpoint.
    
    Validates initData from Telegram Mini App.
    
    Security baseline:
    - STRICT: No DEBUG bypass or hardcoded IDs
    - Whitelist-only: User must exist in DB
    - Returns 401 for invalid auth, 403 for user not found/inactive
    """
    
    # Validate initData
    user_data = validate_telegram_init_data(request.init_data)
    
    if not user_data:
        logger.warning("Failed to validate Telegram initData")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    telegram_user_id = user_data.get("user_id")
    if not telegram_user_id:
        logger.warning("Missing user_id in validated Telegram data")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data"
        )
    
    # P0: Whitelist-only - user MUST exist in DB (no auto-create)
    user = get_user_by_telegram_id(db, telegram_user_id)
    if not user:
        logger.info(f"Authentication attempt for non-whitelisted user {telegram_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not found in system"
        )
    
    if not user.is_active:
        logger.warning(f"Authentication attempt for inactive user {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate JWT token
    token = create_access_token(
        data={
            "user_id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "role": user.role
        }
    )
    
    logger.info(f"Successful authentication for user {user.id} (telegram_id={telegram_user_id})")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    return UserResponse.model_validate(current_user)
