# Telegram Web App Flow

## Описание

Приложение использует Telegram Mini App для авторизации пользователей. Поддерживает три режима работы:

### 1. **Основной режим: Telegram Web App**
Пользователь открывает бота (@coffeekznebot) и запускает Mini App с кнопки.

**Процесс:**
```
1. Пользователь открывает Telegram бота
2. Нажимает на кнопку "Открыть приложение"
3. Открывается Web App с правильными Telegram данными
4. `useTelegram.ts` получает userData и appInitData
5. Авторизация происходит через `/api/v1/auth/telegram` endpoint
6. Пользователь логинится в систему
```

**Код:**
```typescript
// useTelegram.ts - детектирует Web App окружение
if (userData && appInitData) {
  // Реальное Telegram окружение
  setUser(userData);
  setInitData(appInitData);
}
```

### 2. **Режим для обычного браузера: Redirect в Telegram**
Пользователь открывает `https://admin.b2broundtable.ru` с обычного браузера.

**Процесс:**
```
1. Страница загружается, userData = null (не в Telegram)
2. Показывается кнопка "Открыть в Telegram"
3. При клике открывается Telegram бот с Web App:
   https://t.me/coffeekznebot/vendingadmin
4. Бот открывает Web App в Telegram
5. Web App получает правильные userData
6. Пользователь авторизуется и возвращается на сайт
```

**Код:**
```typescript
// LoginPage.tsx
const handleOpenTelegram = () => {
  const telegramUrl = `https://t.me/${TELEGRAM_BOT_USERNAME}/vendingadmin?startapp=login_${Date.now()}`;
  window.location.href = telegramUrl;
};
```

### 3. **Режим разработки: Debug Mode**
Для локальной разработки без необходимости использовать реальный Telegram.

**Как использовать:**
```
https://admin.b2broundtable.ru/login?debug=true
```

**Что происходит:**
- Генерируются тестовые Telegram данные
- Используется test user ID: 602720033 (Roman)
- Полная авторизация работает с test данными
- Можно тестировать на localhost и на production сервере

**Код:**
```typescript
// useTelegram.ts
if (!userData) {
  const isDev = !import.meta.env.PROD;
  const isLocalhost = window.location.hostname === 'localhost';
  const hasDebugParam = new URLSearchParams(window.location.search).has('debug');
  
  if ((isDev && isLocalhost) || hasDebugParam) {
    // Загружаем test данные
    setUser(testUser);
    setInitData(testInitData);
  }
}
```

---

## Архитектура

### Frontend (`useTelegram.ts`)
```
┌─────────────────────────────────────┐
│ Инициализация Telegram WebApp       │
└────────────┬────────────────────────┘
             │
             ▼
      ┌─────────────────┐
      │ userData есть?  │
      └─────────┬───────┘
                │
        ┌───────┴────────┐
        │                │
    YES │                │ NO
        ▼                ▼
   ┌─────────┐    ┌──────────────────┐
   │ Real TG │    │ !userData check  │
   │ Data    │    └────────┬─────────┘
   └─────────┘             │
                    ┌──────┴────────┐
                    │               │
            debug=true │        │ NO
                    ▼               ▼
               ┌─────────┐    ┌──────────┐
               │ Test    │    │ null     │
               │ Data    │    │ initData │
               └─────────┘    └──────────┘
```

### Backend (`auth.py`)
```
POST /api/v1/auth/telegram
├─ Получает initData
├─ Валидирует HMAC подпись
├─ Извлекает telegram_user_id
├─ Проверяет user в DB
├─ Создаёт JWT token
└─ Возвращает token + user info
```

---

## API Endpoints

### POST `/api/v1/auth/telegram`
**Запрос:**
```json
{
  "init_data": "query_id=...&user={...}&auth_date=...&hash=..."
}
```

**Успешный ответ (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "telegram_user_id": 602720033,
    "username": "owner",
    "role": "owner",
    "is_active": true
  }
}
```

**Ошибки:**
- `400`: Невалидные данные или некорректная подпись
- `404`: Пользователь не зарегистрирован в системе

---

## Конфигурация

### Frontend переменные окружения (`.env.production`)
```env
VITE_API_BASE_URL=/api
VITE_TELEGRAM_BOT_USERNAME=coffeekznebot
VITE_ENV=production
```

### Backend переменные
```python
# Telegram Bot токен для валидации initData
TELEGRAM_BOT_TOKEN=<from @BotFather>

# JWT секретный ключ
SECRET_KEY=<random-string>
```

---

## Проблемы и решения

### Проблема: "Network Error" при логине
**Причины:**
1. API базовый URL не настроен (исправлено: используем `/api` как относительный путь)
2. Endpoints имеют дублирование `/api/api` (исправлено: endpoints теперь `/v1/...`)
3. CORS заголовки не настроены (исправлено: Nginx добавляет правильные headers)

**Решение:**
```typescript
// client.ts - использует relative path
const apiClient = axios.create({
  baseURL: '/api',  // Nginx проксирует на backend
});

// auth.ts - endpoint без /api префикса
apiClient.post('/v1/auth/telegram', payload);
```

### Проблема: Debug mode не работает
**Решение:**
- Используем `?debug=true` параметр
- Проверяем только `userData` переменную (не и `appInitData`)
- `appInitData` всегда присутствует как "..." в non-Telegram окружении

### Проблема: Редирект в Telegram не работает
**Решение:**
- Используем правильный format: `https://t.me/bot_username/app_name`
- `app_name` должно быть настроено в BotFather
- Параметр `?startapp=` опционален, но помогает отслеживать источник

---

## Testing

### Локально (development)
```bash
# С debug mode
https://localhost:5173/login?debug=true

# С Docker
https://admin.b2broundtable.ru/login?debug=true
```

### На production
```bash
# Обычный браузер
https://admin.b2broundtable.ru/login

# Debug mode
https://admin.b2broundtable.ru/login?debug=true

# Telegram Web App
https://t.me/coffeekznebot/vendingadmin
```

---

## Безопасность

1. **HMAC Валидация**: Все initData подписаны HMAC-SHA256 с использованием Telegram Bot токена
2. **JWT Токены**: Содержат expiration и подписаны SECRET_KEY
3. **CORS**: Разрешены только запросы с допустимых источников
4. **HTTPS**: Все коммуникации зашифрованы

---

## Миграция в production

Когда Telegram бот будет настроен с правильным Web App URL:

1. **Bot Father конфигурация:**
   - `@BotFather` → `/mybots` → выбрать бота
   - `App menu button` → установить URL: `https://admin.b2broundtable.ru`
   - Web App будет доступен через кнопку в главном меню

2. **Отключить debug mode:**
   - Убрать `?debug=true` параметры
   - Debug mode работает автоматически на localhost

3. **Публикация:**
   - Бот будет доступен всем пользователям
   - Пользователи смогут открыть Web App из Telegram
   - Также смогут открыть с обычного браузера и кликнуть "Открыть в Telegram"
