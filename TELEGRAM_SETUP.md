# Telegram OAuth Setup Guide

Полное руководство по настройке и интеграции Telegram OAuth для Vending Admin v2.

## Table of Contents

1. [Backend Setup](#backend-setup)
2. [Frontend Setup](#frontend-setup)
3. [Testing the Integration](#testing-the-integration)
4. [Troubleshooting](#troubleshooting)

---

## Backend Setup

### 1. Environment Variables

Добавьте в `backend/.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=your_bot_username
```

**Где получить эти значения:**

- **TELEGRAM_BOT_TOKEN**: Получите у [@BotFather](https://t.me/botfather) в Telegram после создания бота
- **TELEGRAM_BOT_USERNAME**: Username вашего бота (без `@`), например `coffeekznebot`

### 2. Database Setup

Убедитесь, что таблица `users` содержит поля:

```python
- telegram_user_id: BigInteger (уникальный)
- role: String ('owner' или 'operator')
- is_active: Boolean
```

Модель уже настроена в [app/models/user.py](../backend/app/models/user.py).

### 3. Запуск Backend

```bash
cd backend
docker compose up -d --build
```

Проверьте, что API доступен:

```bash
curl http://localhost:8000/health
```

---

## Frontend Setup

### 1. Environment Variables

Добавьте в `frontend/.env`:

```env
VITE_API_BASE_URL=/api/v1
VITE_TELEGRAM_BOT_USERNAME=your_bot_username
```

### 2. API Client Configuration

ApiClient уже настроен на `baseURL="/api/v1"` в [src/api/client.ts](../frontend/src/api/client.ts).

### 3. Telegram Login Widget

Виджет автоматически инициализируется на странице логина ([src/pages/LoginPage.tsx](../frontend/src/pages/LoginPage.tsx)):

```typescript
// Viджет использует официальный скрипт:
// https://telegram.org/js/telegram-widget.js

// Callback обработка:
const onTelegramAuth = async (user) => {
  // Отправляем на backend
  const response = await telegramOAuthApi.loginWithTelegramOAuth(user);
  // Сохраняем JWT и пользователя
  setToken(response.access_token);
  setUser(response.user);
  // Редирект в ЛК
  navigate(ROUTES.OVERVIEW);
};
```

### 4. Запуск Frontend

```bash
cd frontend
npm install
npm run dev
```

Откройте [http://localhost:5173](http://localhost:5173).

---

## Testing the Integration

### Browser OAuth Flow

1. Откройте [http://localhost:5173/login](http://localhost:5173/login)
2. На странице вы должны увидеть кнопку **"Войти через Telegram"** (Telegram Login Widget)
3. Нажмите на кнопку
4. Авторизуйтесь в Telegram
5. Виджет вернёт данные (id, hash, auth_date и т.д.)
6. Frontend отправит их на `POST /api/v1/auth/telegram_oauth`

### Backend OAuth Endpoint

**Endpoint:** `POST /api/v1/auth/telegram_oauth`

**Request Body:**
```json
{
  "init_data": "{\"id\":123456789,\"first_name\":\"John\",\"username\":\"johndoe\",\"auth_date\":1673456789,\"hash\":\"...\"}"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "telegram_user_id": 123456789,
    "role": "owner",
    "name": "John Doe",
    "is_active": true
  }
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid or expired hash
- **403 Forbidden** - User not registered or inactive

### Mini App OAuth Flow

Для мобильных приложений (Telegram Web App):

**Endpoint:** `POST /api/v1/auth/telegram`

**Request Body:**
```json
{
  "init_data": "query_id=...&user=...&auth_date=...&hash=..."
}
```

---

## RBAC (Role-Based Access Control)

### User Roles

- **owner** - Владелец, имеет полный доступ ко всем функциям
- **operator** - Оператор, имеет ограниченный доступ

### Protected Endpoints

#### Owner Only

- `GET /api/v1/analytics/owner-report` - Отчёт собственника

Попытка доступа оператора вернёт **403 Forbidden**.

### Frontend Role-Based UI

Navigation items фильтруются по ролям в [src/utils/constants.ts](../frontend/src/utils/constants.ts):

```typescript
NAV_ITEMS = [
  {
    key: 'owner-report',
    label: 'Отчёт собственника',
    roles: ['owner'],  // Only for owners
  },
  {
    key: 'settings',
    label: 'Настройки',
    roles: ['owner'],  // Only for owners
  },
  // ... operator items ...
]
```

---

## Database User Setup

### Creating Users Manually (SQL)

```sql
INSERT INTO users (
  telegram_user_id, username, first_name, last_name, role, is_active
) VALUES 
(
  123456789,           -- Ваш Telegram ID
  'johndoe',           -- Username
  'John',              -- First name
  'Doe',               -- Last name
  'owner',             -- 'owner' или 'operator'
  true                 -- is_active
);
```

**Get your Telegram ID:**
- Open [https://t.me/getmyidbot](https://t.me/getmyidbot) in Telegram
- Bot will send you your ID

### Whitelisting Users

Только пользователи, добавленные в БД, могут войти:

```sql
-- Проверить существующих пользователей
SELECT id, telegram_user_id, first_name, role, is_active FROM users;

-- Добавить пользователя
INSERT INTO users (telegram_user_id, first_name, role, is_active) 
VALUES (123456789, 'John', 'operator', true);

-- Деактивировать пользователя
UPDATE users SET is_active = false WHERE telegram_user_id = 123456789;

-- Изменить роль
UPDATE users SET role = 'owner' WHERE telegram_user_id = 123456789;
```

---

## Security Notes

### ✅ Best Practices Implemented

1. **Hash Validation** - Все данные от Telegram проверяются через HMAC SHA256
2. **Auth Date Check** - Авторизация валидна не более 24 часов
3. **Whitelist Only** - Только пользователи в БД получают доступ
4. **No Hardcoded Backdoors** - Удалены все debug fallback'и
5. **HTTPS in Production** - Используйте HTTPS для боевого окружения
6. **JWT Expiration** - Токены имеют срок действия (по умолчанию 7 дней)

### ⚠️ Important

- **TELEGRAM_BOT_TOKEN** - Храните в .env, никогда не коммитьте в repo
- **SECRET_KEY** - Измените на уникальное значение в production
- **CORS_ORIGINS** - Ограничьте список доменов в production

---

## Troubleshooting

### Issue: "Invalid Telegram authentication data" (401)

**Causes:**
- Hash mismatch (неверный TELEGRAM_BOT_TOKEN)
- auth_date слишком старый (> 24 часов)
- Неверный JSON в init_data

**Fix:**
```bash
# Проверьте TELEGRAM_BOT_TOKEN
grep TELEGRAM_BOT_TOKEN backend/.env

# Убедитесь что время на сервере синхронизировано
date
```

### Issue: "User not found" (403)

**Causes:**
- Пользователь не добавлен в БД
- Пользователь деактивирован (is_active = false)

**Fix:**
```sql
-- Проверьте есть ли пользователь в БД
SELECT * FROM users WHERE telegram_user_id = YOUR_TELEGRAM_ID;

-- Если нет - добавьте
INSERT INTO users (telegram_user_id, first_name, role, is_active) 
VALUES (YOUR_TELEGRAM_ID, 'Name', 'operator', true);
```

### Issue: "Cannot find /api/v1/auth/telegram_oauth"

**Causes:**
- Backend не запущен
- Неверный baseURL в frontend
- CORS issue

**Fix:**
```bash
# Проверьте что backend запущен
curl -i http://localhost:8000/health

# Проверьте CORS в backend
grep CORS_ORIGINS backend/.env

# Проверьте baseURL в frontend
cat frontend/src/api/client.ts | grep baseURL
```

### Issue: "Operator can't access owner reports"

**Expected behavior** - Это правильно! Только владельцы имеют доступ.

**To give operator owner access:**
```sql
UPDATE users SET role = 'owner' WHERE telegram_user_id = YOUR_TELEGRAM_ID;
```

---

## Additional Resources

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Login Widget](https://core.telegram.org/widgets/login)
- [Telegram Web Apps](https://core.telegram.org/bots/webapps)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

## Support

Для вопросов и проблем:

1. Проверьте [DEBUG_GUIDE.md](./DEBUG_GUIDE.md)
2. Посмотрите логи backend: `docker compose logs api`
3. Проверьте browser console (F12) на frontend
4. Убедитесь что переменные окружения установлены

---

**Last Updated:** January 2026
**Version:** 1.0.0
