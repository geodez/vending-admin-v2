# Backend - Vending Admin v2

FastAPI backend с аутентификацией через Telegram Mini App.

## 🚀 Быстрый старт

### Автоматический деплой (рекомендуется)

```bash
# 1. Настроить .env
cp .env.example .env
nano .env  # Укажите TELEGRAM_BOT_TOKEN и SECRET_KEY

# 2. Запустить автоматический деплой
./deploy.sh
```

Скрипт автоматически:
- Запустит Docker Compose (PostgreSQL + FastAPI)
- Применит миграции
- Создаст пользователя Owner (Telegram ID: 602720033)
- Проверит что API работает

### Ручной деплой

#### 1. Настройка .env

```bash
cp .env.example .env
nano .env
```

**Важно:** Обязательно укажите реальный `TELEGRAM_BOT_TOKEN` и `SECRET_KEY`!

#### 2. Запуск через Docker Compose

```bash
docker-compose up -d
```

#### 3. Применить миграции

```bash
docker-compose exec app alembic upgrade head
```

#### 4. Создать пользователя Owner

```bash
docker-compose exec db psql -U vending -d vending < create_owner.sql
```

#### 5. Проверка

API доступен по адресу: http://localhost:8000

- Health check: http://localhost:8000/health
- Connection status: http://localhost:8000/status
- API docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🗄️ База данных

PostgreSQL 16 на порту 5432:

```
Host: localhost
Port: 5432
Database: vending
User: vending
Password: vending_pass
```

---

## 🔐 Аутентификация

### Telegram WebApp Flow

1. Frontend получает `window.Telegram.WebApp.initData`
2. Отправляет на `POST /api/v1/auth/telegram`
3. Backend валидирует через HMAC-SHA256
4. Возвращает JWT токен

### Использование JWT

Все защищенные endpoints требуют заголовок:

```
Authorization: Bearer <JWT_TOKEN>
```

---

## 📋 API Endpoints

### Authentication

- `POST /api/v1/auth/telegram` — аутентификация через Telegram
- `GET /api/v1/auth/me` — текущий пользователь

---

## 🛠️ Миграции Alembic

### Создать новую миграцию

```bash
docker-compose exec app alembic revision --autogenerate -m "description"
```

### Применить миграции

```bash
docker-compose exec app alembic upgrade head
```

### Откатить миграцию

```bash
docker-compose exec app alembic downgrade -1
```

### Посмотреть историю

```bash
docker-compose exec app alembic history
```

---

## 👤 Создание первого пользователя (Owner)

Подключитесь к PostgreSQL и выполните:

```sql
INSERT INTO users (telegram_user_id, username, first_name, role, is_active)
VALUES (123456789, 'your_username', 'Your Name', 'owner', true);
```

Замените `123456789` на ваш реальный Telegram User ID.

**Как узнать свой Telegram User ID:**
1. Откройте бота [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш User ID

---

## 🧪 Тестирование

```bash
# Установить pytest
pip install pytest pytest-asyncio httpx

# Запустить тесты
pytest
```

---

## 📦 Структура проекта

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   └── auth.py          # Auth endpoints
│   │   └── deps.py              # Dependencies (get_current_user)
│   ├── auth/
│   │   ├── telegram.py          # Telegram auth validation
│   │   └── jwt.py               # JWT токены
│   ├── models/
│   │   └── user.py              # User model
│   ├── schemas/
│   │   └── auth.py              # Pydantic schemas
│   ├── crud/
│   │   └── user.py              # CRUD операции
│   ├── db/
│   │   ├── base.py              # SQLAlchemy Base
│   │   └── session.py           # Database session
│   ├── config.py                # Settings
│   └── main.py                  # FastAPI app
├── migrations/                  # Alembic migrations
├── tests/                       # Тесты
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🔧 Полезные команды

### Логи

```bash
# Все сервисы
docker-compose logs -f

# Только app
docker-compose logs -f app

# Только db
docker-compose logs -f db
```

### Рестарт

```bash
docker-compose restart app
```

### Остановка

```bash
docker-compose down
```

### Остановка с удалением данных

```bash
docker-compose down -v
```

---

## 🐛 Troubleshooting

### База данных не подключается

Проверьте что PostgreSQL запущен:

```bash
docker-compose ps
```

### Миграции не применяются

Проверьте что БД создана:

```bash
docker-compose exec db psql -U vending -d vending -c "\dt"
```

### Telegram auth не работает

Проверьте что `TELEGRAM_BOT_TOKEN` указан правильно в `.env`.

---

## 📚 Дополнительно

- [FastAPI документация](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 документация](https://docs.sqlalchemy.org/en/20/)
- [Alembic документация](https://alembic.sqlalchemy.org/)
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
