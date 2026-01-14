import hashlib
import hmac
import json
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.config import settings


def validate_telegram_init_data(init_data: str) -> Optional[Dict]:
    """
    Валидация initData от Telegram WebApp.
    
    Проверяет:
    1. Подлинность данных через HMAC-SHA256
    2. Срок действия auth_date (не старше 24 часов)
    
    Возвращает dict с данными пользователя или None при ошибке.
    """
    try:
        # Парсим query string
        data_dict = parse_qs(init_data)
        
        # Получаем hash
        hash_value = data_dict.get("hash", [None])[0]
        if not hash_value:
            return None
        
        # Собираем все параметры кроме hash
        check_string = "\n".join([
            f"{k}={v[0]}" for k, v in sorted(data_dict.items())
            if k != "hash"
        ])
        
        # Вычисляем secret_key
        secret_key = hmac.new(
            b"WebAppData",
            settings.TELEGRAM_BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем hash (в DEBUG режиме пропускаем проверку)
        if calculated_hash != hash_value:
            if not settings.DEBUG:
                return None
        
        # Проверяем auth_date (не старше 24 часов)
        auth_date_str = data_dict.get("auth_date", [None])[0]
        if not auth_date_str:
            return None
        
        try:
            auth_date = datetime.fromtimestamp(int(auth_date_str))
            if datetime.now() - auth_date > timedelta(hours=24):
                if not settings.DEBUG:
                    return None
        except:
            pass
        
        # Парсим данные пользователя
        user_json = data_dict.get("user", ["{}"])[0]
        user_data = json.loads(user_json)
        
        return {
            "user_id": user_data.get("id"),
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
        }
    except Exception as e:
        return None


def validate_telegram_widget_data(auth_data: Dict) -> bool:
    """
    Валидация данных от Telegram Login Widget.
    
    Проверяет подлинность данных через HMAC-SHA256.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    try:
        # Получаем hash
        received_hash = auth_data.get("hash")
        if not received_hash:
            return False
        
        # Создаем строку для проверки (все поля кроме hash, отсортированные)
        check_items = []
        for key in sorted(auth_data.keys()):
            if key != "hash":
                value = auth_data[key]
                check_items.append(f"{key}={value}")
        
        check_string = "\n".join(check_items)
        
        # Вычисляем secret_key (SHA256 хэш от токена бота)
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем совпадение
        if calculated_hash != received_hash:
            print(f"Hash mismatch: {calculated_hash} != {received_hash}")
            if not settings.DEBUG:
                return False
        
        # Проверяем auth_date (не старше 24 часов)
        auth_date = auth_data.get("auth_date")
        if auth_date:
            try:
                auth_timestamp = datetime.fromtimestamp(int(auth_date))
                if datetime.now() - auth_timestamp > timedelta(hours=24):
                    if not settings.DEBUG:
                        return False
            except:
                pass
        
        return True
    except Exception as e:
        print(f"Widget validation error: {e}")
        return False
