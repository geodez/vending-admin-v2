from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


def get_user_by_telegram_id(db: Session, telegram_user_id: int) -> Optional[User]:
    """Получить пользователя по Telegram user_id"""
    return db.query(User).filter(User.telegram_user_id == telegram_user_id).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    telegram_user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    role: str = "operator"
) -> User:
    """Создать нового пользователя"""
    user = User(
        telegram_user_id=telegram_user_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
