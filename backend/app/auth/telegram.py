import hashlib
import hmac
import json
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
from app.config import settings

logger = logging.getLogger(__name__)


def validate_telegram_login_widget(auth_data: Dict, bot_token: str) -> bool:
    """
    Валидация данных от Telegram Login Widget (браузер).
    
    Проверяет подлинность данных через HMAC-SHA256.
    https://core.telegram.org/widgets/login#checking-authorization
    
    Алгоритм:
    1. Получить все поля кроме hash
    2. Отсортировать по ключу
    3. Создать data_check_string = key1=value1\\nkey2=value2\\n...
    4. secret_key = SHA256(BOT_TOKEN)
    5. computed_hash = HMAC-SHA256(data_check_string, secret_key)
    6. Сравнить с полученным hash
    """
    try:
        # Получаем hash
        received_hash = auth_data.get("hash")
        if not received_hash:
            logger.error("Missing hash in auth_data")
            return False
        
        # Создаем строку для проверки (все поля кроме hash, отсортированные)
        # Пропускаем None значения и hash
        check_items = []
        for key in sorted(auth_data.keys()):
            if key != "hash":
                value = auth_data[key]
                # Пропускаем None значения
                if value is not None:
                    check_items.append(f"{key}={value}")
        
        check_string = "\n".join(check_items)
        
        # Вычисляем secret_key (SHA256 хэш от токена бота)
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Диагностика (безопасное логирование)
        logger.info(
            f"Login Widget validation: "
            f"user_id={auth_data.get('id')}, "
            f"keys={sorted([k for k in auth_data.keys() if k != 'hash'])}, "
            f"data_check_string_length={len(check_string)}, "
            f"calculated_hash={calculated_hash[:8]}..., "
            f"received_hash={received_hash[:8]}..."
        )
        
        # Проверяем совпадение (constant-time comparison)
        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning(
                f"❌ Hash mismatch for user_id={auth_data.get('id')}: "
                f"calculated={calculated_hash[:8]}..., "
                f"received={received_hash[:8]}..."
            )
            return False
        
        logger.info(f"✅ Hash validated for user_id={auth_data.get('id')}")
        
        return True
    except Exception as e:
        logger.error(f"Widget validation error: {e}", exc_info=True)
        return False


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
        logger.error(f"WebApp initData validation error: {e}", exc_info=True)
        return None
