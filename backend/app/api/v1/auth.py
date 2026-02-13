from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.auth.telegram import validate_telegram_init_data, validate_telegram_login_widget
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.crud.user import get_user_by_telegram_id, get_user_by_email, create_user
from app.schemas.auth import (
    TelegramAuthRequest, 
    TelegramLoginWidgetRequest,
    LoginRequest,
    TokenResponse, 
    UserResponse, 
    UserCreate
)
from app.api.deps import get_current_user
from app.models.user import User
from app.config import settings
import hmac
import hashlib
import time
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
def authenticate_with_password(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Аутентификация по email и паролю.
    
    Процесс:
    1. Проверяет существование пользователя по email
    2. Проверяет правильность пароля
    3. Проверяет активность пользователя
    4. Генерирует JWT токен
    
    Возвращает:
    - access_token: JWT токен для доступа к API
    - user: Данные пользователя
    """
    logger.info(f"🔐 Login attempt for email: {request.email}")
    
    # Поиск пользователя по email
    user = get_user_by_email(db, request.email)
    
    if not user:
        logger.warning(f"❌ User not found: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Проверка пароля
    if not user.hashed_password:
        logger.warning(f"❌ User has no password set: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    if not verify_password(request.password, user.hashed_password):
        logger.warning(f"❌ Invalid password for: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # Проверка активности
    if not user.is_active:
        logger.warning(f"❌ User inactive: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    # Генерация JWT токена
    token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }
    )
    
    logger.info(f"✅ Login successful: {request.email}, role={user.role}")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )



@router.post("/telegram_oauth", response_model=TokenResponse)
def authenticate_telegram_oauth(request: TelegramLoginWidgetRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram Login Widget (браузер).
    
    Принимает плоский объект с полями от Telegram Login Widget:
    - id: Telegram user ID
    - first_name: Имя пользователя
    - auth_date: Unix timestamp авторизации
    - hash: HMAC-SHA256 подпись
    - username, last_name, photo_url: опциональные поля
    
    Валидация:
    1. Проверяет HMAC-SHA256 подпись (secret_key = SHA256(BOT_TOKEN))
    2. Проверяет auth_date (не старше 24 часов)
    3. Проверяет наличие пользователя в БД (whitelist)
    4. Генерирует JWT токен
    
    Важно: Это НЕ Telegram WebApp initData! 
    Для WebApp используйте POST /telegram_webapp
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    # Собираем данные для валидации (конвертируем Pydantic model в dict)
    auth_data = request.model_dump(exclude_none=True)
    
    # Диагностика (безопасная - без полных хешей)
    current_time = int(time.time())
    auth_age = current_time - request.auth_date
    
    logger.info(
        f"🔐 Login Widget auth attempt: "
        f"user_id={request.id}, "
        f"auth_age={auth_age}s, "
        f"keys={sorted(auth_data.keys())}, "
        f"hash_prefix={request.hash[:6]}"
    )
    
    # Проверка auth_date (не старше 24 часов)
    if auth_age > 86400:
        logger.warning(
            f"❌ auth_date too old: user_id={request.id}, "
            f"auth_age={auth_age}s ({auth_age/3600:.1f}h)"
        )
        raise HTTPException(
            status_code=401,
            detail="Authentication expired. Please try again."
        )
    
    if auth_age < 0:
        logger.warning(
            f"❌ auth_date in future: user_id={request.id}, auth_age={auth_age}s"
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication timestamp"
        )
    
    # Валидация подписи Telegram Login Widget
    is_valid = validate_telegram_login_widget(auth_data, settings.TELEGRAM_BOT_TOKEN)
    
    if not is_valid:
        logger.warning(
            f"❌ Signature validation failed: user_id={request.id}"
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )
    
    logger.info(f"✅ Signature valid: user_id={request.id}")
    
    # Поиск пользователя в БД
    user = get_user_by_telegram_id(db, request.id)
    
    if not user:
        logger.warning(
            f"❌ User not in whitelist: user_id={request.id}, "
            f"username={request.username or 'N/A'}"
        )
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен"
        )
    
    if not user.is_active:
        logger.warning(f"❌ User inactive: user_id={request.id}")
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен"
        )
    
    # Генерация JWT токена
    token = create_access_token(
        data={
            "user_id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "role": user.role
        }
    )
    
    logger.info(
        f"✅ Login successful: user_id={request.id}, role={user.role}"
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/telegram_oauth")
async def authenticate_telegram_oauth_widget(
    id: int,
    first_name: str,
    hash: str,
    auth_date: int,
    username: Optional[str] = None,
    last_name: Optional[str] = None,
    photo_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Используйте POST /telegram_oauth
    
    Аутентификация через Telegram Login Widget (GET запрос).
    Оставлен только для совместимости, все новые интеграции должны использовать POST.
    """
    raise HTTPException(
        status_code=410,
        detail="This endpoint is deprecated. Use POST /telegram_oauth instead."
    )



@router.post("/telegram_webapp", response_model=TokenResponse)
@router.post("/telegram", response_model=TokenResponse)  # Alias для обратной совместимости
def authenticate_telegram_webapp(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram WebApp (Mini App).
    
    Используется для мини-приложений Telegram. Валидирует initData в формате query-string.
    Для браузерного Login Widget используйте POST /telegram_oauth.
    
    Процесс:
    1. Валидирует initData от Telegram WebApp (query-string формат)
    2. Проверяет существование пользователя в БД (whitelist)
    3. Возвращает JWT токен (если пользователь активен)
    
    Важно: initData должен быть в формате query-string (url-encoded),
    а НЕ плоский JSON объект от Login Widget.
    """
    logger.info("🔐 WebApp auth attempt: validating initData...")
    
    # Валидация initData
    user_data = validate_telegram_init_data(request.init_data)
    
    if not user_data:
        logger.warning("❌ WebApp initData validation failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    telegram_user_id = user_data.get("user_id")
    if not telegram_user_id:
        logger.warning("❌ Missing user_id in validated initData")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    logger.info(f"✅ WebApp initData valid: user_id={telegram_user_id}")
    
    # Поиск пользователя в БД
    user = get_user_by_telegram_id(db, telegram_user_id)
    
    if not user:
        logger.warning(f"❌ User not in whitelist: user_id={telegram_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    if not user.is_active:
        logger.warning(f"❌ User inactive: user_id={telegram_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    # Генерация JWT токена
    token = create_access_token(
        data={
            "user_id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "role": user.role
        }
    )
    
    logger.info(f"✅ WebApp login successful: user_id={telegram_user_id}, role={user.role}")
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Получить информацию о текущем пользователе.
    """
    return UserResponse.model_validate(current_user)
