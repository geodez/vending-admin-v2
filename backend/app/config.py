from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://vending:vending_pass@db:5432/vending"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Vendista API
    vendista_api_base_url: str = "https://api.vendista.ru"
    vendista_api_token: str = ""  # Must be set in .env
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
