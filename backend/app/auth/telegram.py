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
        hash_value = data_dict.get('hash', [None])[0]
        if not hash_value:
            return None
        
        # Собираем все параметры кроме hash
        check_string = '\n'.join([
            f"{k}={v[0]}" for k, v in sorted(data_dict.items())
            if k != 'hash'
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
        
        # Проверяем hash
        if calculated_hash != hash_value:
            return None
        
        # Проверяем auth_date (не старше 24 часов)
        auth_date_str = data_dict.get('auth_date', [None])[0]
        if not auth_date_str:
            return None
        
        auth_date = datetime.fromtimestamp(int(auth_date_str))
        if datetime.now() - auth_date > timedelta(hours=24):
            return None
        
        # Парсим данные пользователя
        user_json = data_dict.get('user', ['{}'])[0]
        user_data = json.loads(user_json)
        
        return {
            'user_id': user_data.get('id'),
            'username': user_data.get('username'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
        }
    except Exception as e:
        print(f"Error validating Telegram initData: {e}")
        return None
