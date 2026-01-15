from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate


def get_user_by_telegram_id(db: Session, telegram_user_id: int) -> Optional[User]:
    """Получить пользователя по Telegram user_id"""
    return db.query(User).filter(User.telegram_user_id == telegram_user_id).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID (alias for compatibility)"""
    return get_user_by_id(db, user_id)


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get list of all users"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    db_user = User(
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
