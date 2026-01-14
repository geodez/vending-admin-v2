from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.auth.telegram import validate_telegram_init_data
from app.auth.jwt import create_access_token
from app.crud.user import get_user_by_telegram_id, create_user
from app.schemas.auth import TelegramAuthRequest, TokenResponse, UserResponse, UserCreate
from app.api.deps import get_current_user
from app.models.user import User
from app.config import settings
import hmac
import hashlib
import time
import json

router = APIRouter()


def validate_telegram_oauth(data: dict, bot_token: str) -> bool:
    '''
    Проверка подписи Telegram OAuth (https://core.telegram.org/widgets/login#checking-authorization)
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


@router.post("/telegram_oauth", response_model=TokenResponse)
def authenticate_telegram_oauth(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram Login Widget (браузер).
    
    Валидирует данные от виджета:
    1. Проверяет подпись (hash)
    2. Проверяет время авторизации (не старше 24ч)
    3. Ищет пользователя в БД
    4. Выдает JWT если пользователь существует и активен
    
    Требования:
    - Невозможно залогиниться без валидного Telegram hash
    - Пользователь отсутствует в БД → 403 "Доступ запрещен"
    - Пользователь неактивен → 403 "Доступ запрещен"
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot token not configured")
    
    # Парсим данные от виджета
    try:
        user_data = json.loads(request.init_data) if isinstance(request.init_data, str) else request.init_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    if not isinstance(user_data, dict):
        raise HTTPException(status_code=400, detail="Expected dict from init_data")
    
    # Извлекаем обязательные поля
    telegram_user_id = user_data.get("id")
    hash_value = user_data.get("hash")
    auth_date = user_data.get("auth_date")
    
    if not telegram_user_id or not hash_value or not auth_date:
        raise HTTPException(
            status_code=401,
            detail="Доступ запрещен"
        )
    
    # Валидация подписи Telegram Login Widget
    if not validate_telegram_oauth(user_data, settings.TELEGRAM_BOT_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Доступ запрещен"
        )
    
    # Проверка времени авторизации (не старше 24 часов)
    current_time = int(time.time())
    if current_time - auth_date > 86400:  # 24 * 60 * 60
        raise HTTPException(
            status_code=401,
            detail="Доступ запрещен"
        )
    
    # Поиск пользователя в БД
    user = get_user_by_telegram_id(db, telegram_user_id)
    
    # Если пользователя нет → 403
    if not user:
        raise HTTPException(
            status_code=403,
            detail="Доступ запрещен"
        )
    
    # Если пользователь неактивен → 403
    if not user.is_active:
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



@router.post("/telegram", response_model=TokenResponse)
def authenticate_telegram(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram Mini App.
    
    Используется для мини-приложений Telegram. Валидирует initData.
    Для браузерного входа используйте POST /telegram_oauth.
    
    Процесс:
    1. Валидирует initData от Telegram
    2. Проверяет существование пользователя в БД
    3. Возвращает JWT токен (если пользователь активен)
    """
    # Валидация initData
    user_data = validate_telegram_init_data(request.init_data)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    telegram_user_id = user_data.get("user_id")
    if not telegram_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    # Поиск пользователя в БД
    user = get_user_by_telegram_id(db, telegram_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен"
        )
    
    if not user.is_active:
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
