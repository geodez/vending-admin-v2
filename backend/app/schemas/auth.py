from pydantic import BaseModel
from typing import Optional


class TelegramAuthRequest(BaseModel):
    """Запрос аутентификации через Telegram WebApp (initData query-string)"""
    init_data: str


class TelegramLoginWidgetRequest(BaseModel):
    """Запрос аутентификации через Telegram Login Widget (браузер)"""
    id: int
    first_name: str
    auth_date: int
    hash: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None


class UserResponse(BaseModel):
    """Данные пользователя в ответе"""
    id: int
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "operator"


class TokenResponse(BaseModel):
    """Ответ с JWT токеном"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
