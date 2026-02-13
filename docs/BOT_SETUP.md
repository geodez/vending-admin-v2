# Telegram Bot Setup Guide

## Быстрая настройка бота для Web App

### Шаг 1: Создать/выбрать бота в @BotFather

```
1. Откройте @BotFather в Telegram
2. Нажмите /mybots
3. Выберите существующего бота или создайте нового
```

### Шаг 2: Установить Web App

**Через @BotFather:**
```
/mybots → выбрать бота → App menu button → Установить URL
```

**URL для установки:**
```
https://admin.b2broundtable.ru
```

### Шаг 3: Настроить Web App в BotFather

**Полная настройка:**
```
1. /mybots → выбрать бота → Web App Settings
2. URL для Web App: https://admin.b2broundtable.ru
3. Опционально:
   - Short name: vendingadmin
   - Description: Vending Admin System
```

### Шаг 4: Получить Bot Token

```
/mybots → выбрать бота → API Token
Token формат: 123456789:ABCdefGHIjklmno...
```

Добавить в `.env.production` на backend:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmno...
```

---

## Проверка конфигурации

### Тест 1: Бот доступен
```bash
curl -s https://api.telegram.org/bot<TOKEN>/getMe | jq .
# Должен вернуть информацию о боте
```

### Тест 2: Web App открывается
```
1. Откройте @coffeekznebot (или ваш бот)
2. Должна быть кнопка "App menu button" в меню
3. При клике открывается Web App
```

### Тест 3: Авторизация работает
```
1. Откройте бота, запустите Web App
2. На странице входа должно быть имя пользователя
3. При клике "Войти" должна произойти авторизация
```

---

## Troubleshooting

### Проблема: Web App не открывается
**Решение:**
1. Проверить API Token через `getMe`
2. Убедиться что URL верный и доступен
3. Перезагрузить бота в BotFather

### Проблема: "User not registered"
**Решение:**
1. Убедиться что telegram_user_id зарегистрирован в DB
2. Проверить валидность HMAC подписи
3. Посмотреть логи backend

### Проблема: Redirect в Telegram не работает
**Решение:**
1. Используйте правильный формат: `https://t.me/bot_username/app_name`
2. Убедитесь что `app_name` совпадает с настройками BotFather
3. Параметр `?startapp=` опционален

---

## Переменные окружения

### Backend (`.env`)
```env
# Telegram Bot Token (для валидации initData)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmno...

# JWT Secret (для подписания токенов)
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost/vending_admin

# API
API_BASE_URL=https://api.b2broundtable.ru
```

### Frontend (`.env.production`)
```env
# API базовый путь (Nginx проксирует /api на backend)
VITE_API_BASE_URL=/api

# Telegram бот юзернейм
VITE_TELEGRAM_BOT_USERNAME=coffeekznebot

# Окружение
VITE_ENV=production
```

---

## Production Checklist

- [ ] Bot Token установлен в backend `.env`
- [ ] Web App URL настроен в @BotFather
- [ ] HTTPS сертификат валиден
- [ ] Nginx правильно проксирует `/api` на backend
- [ ] CORS headers настроены
- [ ] JWT SECRET_KEY установлен
- [ ] Database migrations выполнены
- [ ] Test user создан (если требуется)
- [ ] Логирование включено (для debug)
- [ ] Backup database создан

---

## Полезные команды

### Тестирование API
```bash
# Проверить Bot Token
curl -s https://api.telegram.org/bot<TOKEN>/getMe | jq .

# Проверить API доступность
curl https://admin.b2broundtable.ru/api/v1/auth/telegram

# Посмотреть логи backend
docker logs vending-admin-backend

# Посмотреть логи frontend
docker logs -f vending-admin-frontend
```

### Регистрация нового пользователя
```bash
# На сервере
ssh root@155.212.160.190

# Подключиться к postgres
psql postgresql://user:pass@localhost/vending_admin

# Добавить пользователя
INSERT INTO users (telegram_user_id, username, role)
VALUES (602720033, 'roman', 'owner');
```

---

## Дополнительные ресурсы

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram Web Apps](https://core.telegram.org/bots/webapps)
- [BotFather Commands](https://core.telegram.org/bots#botfather)
