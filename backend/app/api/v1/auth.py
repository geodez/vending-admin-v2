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
def authenticate_telegram_oauth_post(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram Login Widget (POST запрос от фронтенда).
    
    Принимает данные пользователя от виджета через frontend callback.
    """
    # Парсим данные пользователя из init_data
    try:
        user_data = json.loads(request.init_data)
    except:
        # Если это не JSON, пытаемся использовать как есть
        user_data = request.init_data if isinstance(request.init_data, dict) else {}
    
    # Валидируем данные
    from app.auth.telegram import validate_telegram_widget_data
    try:
        is_valid = validate_telegram_widget_data(user_data)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid Telegram authentication")
    except Exception as e:
        print(f"Validation error: {e}")
        if not settings.DEBUG:
            raise HTTPException(status_code=401, detail=f"Telegram auth validation failed: {str(e)}")
    
    telegram_user_id = user_data.get("id")
    if not telegram_user_id:
        raise HTTPException(status_code=400, detail="No Telegram user id")
    
    # Поиск или создание пользователя
    user = get_user_by_telegram_id(db, telegram_user_id)
    if not user:
        user_in = UserCreate(
            telegram_user_id=telegram_user_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            role="operator"
        )
        user = create_user(db, user_in)
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
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
    Аутентификация через Telegram Login Widget (GET запрос).
    
    Telegram Widget отправляет GET запрос с параметрами пользователя.
    После успешной авторизации перенаправляем на фронтенд с токеном.
    """
    from urllib.parse import urlencode
    
    # Собираем данные для валидации
    auth_data = {
        "id": id,
        "first_name": first_name,
        "auth_date": auth_date,
        "hash": hash
    }
    if username:
        auth_data["username"] = username
    if last_name:
        auth_data["last_name"] = last_name
    if photo_url:
        auth_data["photo_url"] = photo_url
    
    # Валидируем данные
    try:
        from app.auth.telegram import validate_telegram_widget_data
        is_valid = validate_telegram_widget_data(auth_data)
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid Telegram authentication")
    except Exception as e:
        print(f"Validation error: {e}")
        raise HTTPException(status_code=401, detail=f"Telegram auth validation failed: {str(e)}")
    
    # Поиск или создание пользователя
    user = get_user_by_telegram_id(db, id)
    if not user:
        user_in = UserCreate(
            telegram_user_id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role="operator"
        )
        user = create_user(db, user_in)
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Генерация JWT токена
    token = create_access_token(
        data={
            "user_id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "role": user.role
        }
    )
    
    # Перенаправляем на фронтенд с токеном в URL
    from fastapi.responses import RedirectResponse
    frontend_url = f"/login?token={token}&user_id={user.id}&username={username or ''}"
    return RedirectResponse(url=frontend_url)


@router.post("/telegram_oauth_old", response_model=TokenResponse)
def authenticate_telegram_oauth(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram OAuth (браузер).
    1. Валидация подписи Telegram
    2. Поиск или создание пользователя
    3. Возврат JWT токена
    """
    try:
        oauth_data = json.loads(request.init_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid OAuth data format")

    # Проверка подписи
    if not validate_telegram_oauth(oauth_data, settings.TELEGRAM_BOT_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid Telegram OAuth signature")

    telegram_user_id = oauth_data.get("id")
    if not telegram_user_id:
        raise HTTPException(status_code=400, detail="No Telegram user id")

    # Поиск пользователя
    user = get_user_by_telegram_id(db, telegram_user_id)
    if not user:
        # Создаём пользователя
        user_in = UserCreate(
            telegram_user_id=telegram_user_id,
            username=oauth_data.get("username"),
            first_name=oauth_data.get("first_name"),
            last_name=oauth_data.get("last_name"),
            role="operator"
        )
        user = create_user(db, user_in)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

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


@router.post("/telegram", response_model=TokenResponse)
def authenticate_telegram(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram Mini App.
    
    1. Валидирует initData от Telegram
    2. Проверяет существование пользователя в БД
    3. Возвращает JWT токен
    """
    print(f"DEBUG: Получен initData: {request.init_data[:100]}...")
    
    # Валидация initData
    user_data = validate_telegram_init_data(request.init_data)
    
    print(f"DEBUG: Результат валидации Telegram: {user_data}")
    
    if not user_data:
        print("DEBUG: user_data is None, пытаемся использовать hardcoded ID в DEBUG режиме")
        # В DEBUG режиме используем hardcoded ID для тестирования
        if settings.DEBUG:
            telegram_user_id = 602720033
            print(f"DEBUG: Используем hardcoded ID: {telegram_user_id}")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram authentication data"
            )
    else:
        telegram_user_id = user_data.get("user_id")
        print(f"DEBUG: user_id из user_data: {telegram_user_id}")
        if not telegram_user_id:
            print("DEBUG: user_id is None, пытаемся использовать hardcoded ID в DEBUG режиме")
            if settings.DEBUG:
                telegram_user_id = 602720033
                print(f"DEBUG: Используем hardcoded ID: {telegram_user_id}")
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Telegram authentication data"
                )
    
    print(f"DEBUG: Ищем пользователя с telegram_user_id: {telegram_user_id}")
    
    # Поиск пользователя в БД
    user = get_user_by_telegram_id(db, telegram_user_id)
    
    print(f"DEBUG: Результат поиска пользователя: {user}")
    
    if not user:
        print(f"DEBUG: Пользователь не найден! telegram_user_id={telegram_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not registered in the system"
        )
    
    if not user.is_active:
        print(f"DEBUG: Пользователь неактивен!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    print(f"DEBUG: Генерируем JWT токен для пользователя {user.id}")
    
    # Генерация JWT токена
    token = create_access_token(
        data={
            "user_id": user.id,
            "telegram_user_id": user.telegram_user_id,
            "role": user.role
        }
    )
    
    print(f"DEBUG: JWT токен успешно сгенерирован")
    
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
