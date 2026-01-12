from pydantic import BaseModel
from typing import Optional


class TelegramAuthRequest(BaseModel):
    """Запрос аутентификации через Telegram"""
    init_data: str


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


class TokenResponse(BaseModel):
    """Ответ с JWT токеном"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
