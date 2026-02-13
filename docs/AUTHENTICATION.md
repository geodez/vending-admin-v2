# Руководство по авторизации в Vending Admin v2

## Обзор

Система поддерживает два способа авторизации:
1. **Telegram** - через Telegram Login Widget или Mini App
2. **Email/Пароль** - традиционная авторизация

## 1. Исправление ошибки "Bot domain invalid"

### Проблема
При попытке войти через Telegram в браузере появляется ошибка "Bot domain invalid".

### Решение
Необходимо настроить домен в BotFather:

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/setdomain`
3. Выберите вашего бота (`@coffeekznebot`)
4. Укажите домен БЕЗ протокола:
   - Для production: `romanrazdobreev.store`
   - Для разработки: используйте ngrok или другой туннель

**Важно:**
- Домен должен быть указан БЕЗ `https://` или `http://`
- Telegram разрешает только ОДИН домен
- Для `localhost` может потребоваться туннель (ngrok)

## 2. Авторизация по Email/Паролю

### Настройка

#### Шаг 1: Установите зависимости
```bash
cd backend
pip install -r requirements.txt
```

#### Шаг 2: Примените миграцию базы данных
```bash
# В Docker контейнере
docker-compose exec backend alembic upgrade head

# Или локально
cd backend
alembic upgrade head
```

#### Шаг 3: Создайте пользователя с паролем

Используйте Python скрипт для создания пользователя:

```python
from app.db.session import SessionLocal
from app.crud.user import create_user
from app.schemas.auth import UserCreate

db = SessionLocal()

# Создание пользователя
user = create_user(
    db,
    UserCreate(
        email="admin@example.com",
        password="secure_password_123",
        first_name="Администратор",
        role="owner",  # или "operator"
    )
)

print(f"Пользователь создан: {user.email}")
db.close()
```

Или через SQL:

```sql
-- Сначала нужно захешировать пароль через Python:
-- from app.auth.password import get_password_hash
-- hashed = get_password_hash("your_password")

INSERT INTO users (email, hashed_password, first_name, role, is_active, created_at, updated_at)
VALUES (
    'admin@example.com',
    '$2b$12$...', -- хешированный пароль
    'Администратор',
    'owner',
    true,
    NOW(),
    NOW()
);
```

### Использование

1. Откройте страницу входа
2. Переключитесь на вкладку "📧 Email"
3. Введите email и пароль
4. Нажмите "Войти"

## 3. Разделение прав доступа

Система поддерживает две роли:

### Owner (Владелец)
Полный доступ ко всем разделам:
- ✅ Обзор
- ✅ Продажи
- ✅ Склад
- ✅ Рецепты
- ✅ Ингредиенты
- ✅ Шаблоны матриц
- ✅ Расходы
- ✅ Настройки

### Operator (Оператор)
Ограниченный доступ:
- ✅ Обзор
- ✅ Продажи
- ✅ Склад
- ✅ Рецепты
- ✅ Ингредиенты
- ❌ Шаблоны матриц
- ✅ Расходы
- ❌ Настройки

Роль указывается при создании пользователя в поле `role`.

## 4. API Endpoints

### POST /api/v1/auth/login
Авторизация по email/паролю

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "secure_password_123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Администратор",
    "role": "owner",
    "is_active": true
  }
}
```

### POST /api/v1/auth/telegram_oauth
Авторизация через Telegram Login Widget

### POST /api/v1/auth/telegram
Авторизация через Telegram Mini App

### GET /api/v1/auth/me
Получить информацию о текущем пользователе

## 5. Переменные окружения

### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/vending

# JWT
SECRET_KEY=your-super-secret-key-change-me-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_BOT_USERNAME=coffeekznebot

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### Frontend (.env)
```env
VITE_API_BASE_URL=https://romanrazdobreev.store/api
VITE_TELEGRAM_BOT_USERNAME=coffeekznebot
VITE_ENV=production
```

## 6. Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены имеют срок действия 7 дней
- Telegram данные валидируются через HMAC-SHA256
- Поддерживается whitelist пользователей (проверка в БД)

## 7. Troubleshooting

### "Bot domain invalid"
→ Настройте домен в BotFather (см. раздел 1)

### "Неверный email или пароль"
→ Проверьте правильность учетных данных
→ Убедитесь, что пользователь создан в БД

### "Доступ запрещен"
→ Пользователь не найден в whitelist (БД)
→ Пользователь неактивен (`is_active = false`)

### Миграция не применяется
```bash
# Проверьте текущую версию
alembic current

# Примените все миграции
alembic upgrade head

# Откатите последнюю миграцию
alembic downgrade -1
```

## 8. Создание скрипта для добавления пользователей

Создайте файл `backend/scripts/create_user.py`:

```python
#!/usr/bin/env python3
"""
Скрипт для создания пользователя с email/паролем
"""
import sys
from app.db.session import SessionLocal
from app.crud.user import create_user, get_user_by_email
from app.schemas.auth import UserCreate

def main():
    if len(sys.argv) < 4:
        print("Usage: python create_user.py <email> <password> <role> [first_name]")
        print("Example: python create_user.py admin@example.com password123 owner Admin")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    role = sys.argv[3]
    first_name = sys.argv[4] if len(sys.argv) > 4 else email.split('@')[0]
    
    if role not in ['owner', 'operator']:
        print("Error: role must be 'owner' or 'operator'")
        sys.exit(1)
    
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли пользователь
        existing = get_user_by_email(db, email)
        if existing:
            print(f"Error: User with email {email} already exists")
            sys.exit(1)
        
        # Создаем пользователя
        user = create_user(
            db,
            UserCreate(
                email=email,
                password=password,
                first_name=first_name,
                role=role,
            )
        )
        
        print(f"✅ User created successfully!")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.first_name}")
        print(f"   Role: {user.role}")
        print(f"   ID: {user.id}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
```

Использование:
```bash
cd backend
python scripts/create_user.py admin@example.com SecurePass123 owner "Администратор"
```
