from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=True, index=True)  # Nullable для пользователей без Telegram
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Поля для авторизации по логину/паролю
    email = Column(String, unique=True, nullable=True, index=True)  # Email для входа
    hashed_password = Column(String, nullable=True)  # Хешированный пароль
    
    role = Column(String, nullable=False, default="operator")  # 'owner' or 'operator'
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_user_id={self.telegram_user_id}, role={self.role})>"
