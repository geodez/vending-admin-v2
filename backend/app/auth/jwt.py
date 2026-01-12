from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from app.config import settings


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT токена.
    
    Args:
        data: Данные для токена (user_id, role, etc.)
        expires_delta: Время жизни токена (если None, берется из настроек)
    
    Returns:
        JWT токен строкой
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """
    Проверка и декодирование JWT токена.
    
    Args:
        token: JWT токен строкой
    
    Returns:
        Payload токена (dict) или None при ошибке
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
