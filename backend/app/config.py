from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import List
import sys


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://vending:vending_pass@db:5432/vending"
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_BOT_USERNAME: str = ""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    # Vendista API
    vendista_api_base_url: str = "https://api.vendista.ru"
    vendista_api_token: str = ""  # Must be set in .env
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @field_validator("TELEGRAM_BOT_USERNAME", mode="after")
    @classmethod
    def validate_telegram_username(cls, v):
        """Ensure Telegram bot username is set in production"""
        if not v or not v.strip():
            raise ValueError("TELEGRAM_BOT_USERNAME must be set in .env")
        return v.lstrip("@")  # Remove @ prefix if present
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    def validate_production_security(self):
        """Validate security baseline for production"""
        if not self.DEBUG:  # Production mode
            errors = []
            
            # Check SECRET_KEY is changed from default
            if self.SECRET_KEY == "your-super-secret-key-change-me-in-production":
                errors.append("SECRET_KEY: Must be changed from default in production")
            
            # Check DEBUG is False
            if self.DEBUG:
                errors.append("DEBUG: Must be False in production")
            
            # Check CORS is restricted
            if self.CORS_ORIGINS == "*":
                errors.append("CORS_ORIGINS: Must not be * in production (currently: '*')")
            
            # Check TELEGRAM_BOT_TOKEN is set
            if not self.TELEGRAM_BOT_TOKEN:
                errors.append("TELEGRAM_BOT_TOKEN: Must be set in production")
            
            # Check TELEGRAM_BOT_USERNAME is set
            if not self.TELEGRAM_BOT_USERNAME:
                errors.append("TELEGRAM_BOT_USERNAME: Must be set in production")
            
            if errors:
                error_msg = "\n".join([f"  ❌ {err}" for err in errors])
                raise ValueError(
                    f"\n❌ PRODUCTION SECURITY BASELINE VIOLATIONS:\n{error_msg}\n"
                    "Refusing to start application. Fix .env file and restart."
                )


settings = Settings()

# Validate production security on startup if DEBUG is False
if not settings.DEBUG:
    try:
        settings.validate_production_security()
        print("✅ Production security baseline validation passed")
    except ValueError as e:
        print(str(e))
        sys.exit(1)
