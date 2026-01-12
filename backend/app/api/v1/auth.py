from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.auth.telegram import validate_telegram_init_data
from app.auth.jwt import create_access_token
from app.crud.user import get_user_by_telegram_id
from app.schemas.auth import TelegramAuthRequest, TokenResponse, UserResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/telegram", response_model=TokenResponse)
def authenticate_telegram(request: TelegramAuthRequest, db: Session = Depends(get_db)):
    """
    Аутентификация через Telegram Mini App.
    
    1. Валидирует initData от Telegram
    2. Проверяет существование пользователя в БД
    3. Возвращает JWT токен
    """
    # Валидация initData
    user_data = validate_telegram_init_data(request.init_data)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Telegram authentication data"
        )
    
    telegram_user_id = user_data['user_id']
    
    # Поиск пользователя в БД
    user = get_user_by_telegram_id(db, telegram_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not registered in the system"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
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
