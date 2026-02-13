# Логика авторизации в Vending Admin v2

## Общий обзор

Приложение использует **Telegram Mini App** для авторизации. Пользователь логинится через Telegram, и система проверяет его идентичность через подпись от Telegram.

---

## Поток авторизации пользователя

```
┌─────────────┐
│  Telegram   │
│  Mini App   │
└──────┬──────┘
       │ 1. Пользователь открывает приложение
       │ 2. Telegram передает initData (подписанные данные)
       │
       ▼
┌──────────────────────┐
│   Frontend (React)   │
│   LoginPage.tsx      │
└──────┬───────────────┘
       │ 3. Получает initData через useTelegram hook
       │ 4. Пользователь нажимает "Войти"
       │
       ▼
┌──────────────────────┐
│  authApi.loginWith   │
│  Telegram(initData)  │
└──────┬───────────────┘
       │ 5. POST /api/v1/auth/telegram
       │
       ▼
┌──────────────────────┐
│  Backend (FastAPI)   │
│  auth.py:            │
│  authenticate_...    │
└──────┬───────────────┘
       │
       ├─ 6. validate_telegram_init_data()
       │
       ├─ 7. Проверка в БД (get_user_by_telegram_id)
       │
       ├─ 8. Создание JWT токена (create_access_token)
       │
       └─ 9. Возврат TokenResponse
              (access_token + user данные)
       │
       ▼
┌──────────────────────┐
│   Frontend (React)   │
│   authStore.ts       │
└──────┬───────────────┘
       │ 10. Сохраняет токен в localStorage
       │ 11. Сохраняет user данные в localStorage
       │ 12. Устанавливает isAuthenticated = true
       │
       ▼
┌──────────────────────┐
│  Защищенные эндпойнты│
│  (с Bearer токеном)  │
└──────────────────────┘
```

---

## Детальное описание каждого этапа

### 1. **Фронтенд: Инициализация Telegram (useTelegram.ts)**

```typescript
// useTelegram hook инициализирует Telegram WebApp
WebApp.ready();           // Сигнал, что приложение готово
WebApp.expand();          // Раскрывает приложение на весь экран

// Получает подписанные данные и информацию о пользователе
const userData = WebApp.initDataUnsafe.user;  // {id, first_name, ...}
const initData = WebApp.initData;             // Подписанная строка
```

**Что такое `initData`?**
- Это URL-encoded строка, которую Telegram генерирует при каждом открытии приложения
- Содержит информацию о пользователе, чате и подпись для верификации
- Пример: `query_id=...&user={"id":123,...}&auth_date=1234567890&hash=abc123`

---

### 2. **Фронтенд: Страница входа (LoginPage.tsx)**

```typescript
const handleLogin = async () => {
  // 1. Проверяет наличие initData
  if (!initData) {
    setError('Telegram данные недоступны...');
    return;
  }

  // 2. Отправляет запрос на бэкенд
  const response = await authApi.loginWithTelegram(initData);
  
  // 3. Сохраняет результат в хранилище
  setToken(response.access_token);
  setUser(response.user);
  
  // 4. Перенаправляет на главную страницу
  navigate(ROUTES.OVERVIEW);
};
```

---

### 3. **API запрос (auth.ts)**

```typescript
loginWithTelegram: async (initData: string) => {
  // Отправляет POST запрос на бэкенд
  const response = await apiClient.post<TokenResponse>(
    '/api/v1/auth/telegram',  // Эндпойнт
    { init_data: initData }    // Payload с подписанными данными
  );
  return response.data;  // Возвращает токен и информацию пользователя
};
```

---

### 4. **Бэкенд: Валидация Telegram (telegram.py)**

Это самая критичная часть! Проверяет подлинность данных от Telegram.

```python
def validate_telegram_init_data(init_data: str):
    """
    Процесс валидации:
    """
    # 1. Парсит query string
    data_dict = parse_qs(init_data)
    
    # 2. Извлекает hash (подпись от Telegram)
    hash_value = data_dict.get("hash")
    
    # 3. Собирает check_string из остальных параметров (без hash)
    check_string = "\n".join([f"{k}={v}" ...])
    
    # 4. Вычисляет secret_key (производный ключ)
    secret_key = hmac.new(
        b"WebAppData",
        TELEGRAM_BOT_TOKEN.encode(),  # Берется из .env
        hashlib.sha256
    ).digest()
    
    # 5. Вычисляет ожидаемый hash с этим ключом
    calculated_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # 6. Сравнивает с полученным hash
    if calculated_hash != hash_value:
        return None  # Невалидные данные!
    
    # 7. Проверяет срок действия (не старше 24 часов)
    auth_date = datetime.fromtimestamp(auth_date_str)
    if datetime.now() - auth_date > timedelta(hours=24):
        return None
    
    # 8. Парсит и возвращает данные пользователя
    user_data = json.loads(data_dict["user"])
    return {"user_id": user_data["id"], ...}
```

**Почему это безопасно?**
- Только Telegram может создать корректный `hash`, потому что он знает `TELEGRAM_BOT_TOKEN`
- Если кто-то попытается подделать данные - хеш не совпадет
- Проверка `auth_date` предотвращает replay-атаки (повторное использование старых токенов)

---

### 5. **Бэкенд: Проверка пользователя в БД (auth.py)**

```python
# После успешной валидации Telegram:

# 1. Ищет пользователя в БД по telegram_user_id
user = get_user_by_telegram_id(db, telegram_user_id)

# 2. Если пользователя нет в БД - ошибка 403
if not user:
    raise HTTPException(
        status_code=403,
        detail="User not registered in the system"
    )

# 3. Если пользователь деактивирован - ошибка 403
if not user.is_active:
    raise HTTPException(
        status_code=403,
        detail="User account is inactive"
    )
```

**Важно!** Пользователь должен быть предварительно добавлен в БД. Это делается администратором через скрипт `create_owner.sql` или команды.

---

### 6. **Бэкенд: Создание JWT токена (jwt.py)**

```python
def create_access_token(data: Dict):
    """
    Создает JWT токен со следующей информацией:
    """
    to_encode = {
        "user_id": user.id,
        "telegram_user_id": user.telegram_user_id,
        "role": user.role,  # 'owner' или 'operator'
        "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    }
    
    # Кодирует в JWT с использованием SECRET_KEY
    token = jwt.encode(
        to_encode,
        SECRET_KEY,      # Из .env
        algorithm="HS256"
    )
    return token  # Возвращает строку вроде "eyJhbGc..."
```

**Жизненный цикл токена:**
- По умолчанию живет **30 дней** (настраивается в config.py)
- Хранится на фронтенде в `localStorage`
- Отправляется в заголовке `Authorization: Bearer <token>` при каждом запросе
- Когда истекает - пользователь нужно переавторизировать

---

### 7. **Ответ на фронтенд (TokenResponse)**

```python
# Бэкенд возвращает:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "telegram_user_id": 602720033,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "role": "owner",
    "is_active": true,
    "created_at": "2024-01-13T10:00:00",
    "updated_at": "2024-01-13T10:00:00"
  }
}
```

---

### 8. **Фронтенд: Сохранение в хранилище (authStore.ts)**

```typescript
// Zustand store сохраняет данные в localStorage

setToken(response.access_token);
// Сохраняет: localStorage.setItem("TOKEN_KEY", "eyJhbGc...")

setUser(response.user);
// Сохраняет: localStorage.setItem("USER_KEY", JSON.stringify(user))

// Устанавливает флаг
isAuthenticated = true
```

**При каждом открытии приложения:**
```typescript
initAuth() {
  const token = localStorage.getItem(TOKEN_KEY);
  const user = localStorage.getItem(USER_KEY);
  
  if (token && user) {
    // Восстанавливает сессию
    set({ token, user, isAuthenticated: true });
  }
}
```

---

### 9. **Защита защищенных эндпойнтов (deps.py)**

Для всех приватных эндпойнтов используется зависимость `get_current_user`:

```python
@router.get("/api/v1/users/me")
def get_current_user(current_user: User = Depends(get_current_user)):
    """
    get_current_user:
    1. Извлекает Bearer токен из заголовка Authorization
    2. Декодирует JWT токен
    3. Получает user_id из токена
    4. Ищет пользователя в БД
    5. Возвращает объект User (или 401 если ошибка)
    """
    return current_user
```

**Пример клиентского запроса:**
```bash
curl -H "Authorization: Bearer eyJhbGc..." https://api.example.com/api/v1/users/me
```

---

## Ключевые файлы и их роли

| Файл | Роль |
|------|------|
| [frontend/src/pages/LoginPage.tsx](frontend/src/pages/LoginPage.tsx) | UI логин страница, инициирует запрос |
| [frontend/src/hooks/useTelegram.ts](frontend/src/hooks/useTelegram.ts) | Получает initData от Telegram |
| [frontend/src/api/auth.ts](frontend/src/api/auth.ts) | HTTP запросы к API |
| [frontend/src/store/authStore.ts](frontend/src/store/authStore.ts) | Zustand стор для состояния авторизации |
| [backend/app/api/v1/auth.py](backend/app/api/v1/auth.py) | POST /api/v1/auth/telegram эндпойнт |
| [backend/app/auth/telegram.py](backend/app/auth/telegram.py) | Валидация Telegram initData |
| [backend/app/auth/jwt.py](backend/app/auth/jwt.py) | Создание и проверка JWT токенов |
| [backend/app/api/deps.py](backend/app/api/deps.py) | Зависимость для защиты эндпойнтов |

---

## Переменные окружения (**.env**)

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# JWT
SECRET_KEY=your-secret-key-keep-it-safe
ACCESS_TOKEN_EXPIRE_DAYS=30
ALGORITHM=HS256

# Debug режим (отключает проверку hash и auth_date)
DEBUG=true
```

---

## Обработка ошибок при авторизации

| Код | Причина | Решение |
|-----|---------|----------|
| 401 | Невалидные Telegram данные | Проверить что `initData` генерируется корректно |
| 403 | Пользователь не зарегистрирован в БД | Добавить пользователя через SQL скрипт |
| 403 | Пользователь деактивирован | Активировать в БД (`is_active = true`) |
| 401 | Истекший токен | Пользователь должен переавторизироваться |
| 401 | Невалидный токен | Проверить что `SECRET_KEY` совпадает |

---

## DEBUG режим

Когда `DEBUG=true` в .env:
- ✅ Валидация hash пропускается
- ✅ Проверка auth_date пропускается (24 часа)
- ✅ Если user_id не найден в initData, используется hardcoded ID: `602720033`

**Это удобно для локальной разработки, но НИКОГДА не использовать в production!**

---

## Безопасность

1. **HTTPS только** - Токены должны передаваться только через защищенное соединение
2. **Secure cookies** - Токены лучше хранить в httpOnly cookies (если не Mini App)
3. **Проверка CORS** - Только доверенные домены могут делать запросы
4. **Валидация на бэкенде** - Никогда не доверять фронтенду без проверки
5. **Проверка роли** - Некоторые эндпойнты требуют роль `owner` (см. `require_owner` в deps.py)

---

## Резюме

Авторизация в приложении построена на **доверии к Telegram**:
1. Telegram подписывает данные `initData`
2. Бэкенд проверяет подпись (только Telegram может ее создать)
3. Если подпись валидна и пользователь в БД - выдается JWT токен
4. Токен используется для защиты остальных эндпойнтов

Это очень безопасный и удобный способ авторизации для Telegram Mini Apps!
