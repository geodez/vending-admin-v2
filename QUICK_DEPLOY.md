# ⚡ Быстрый деплой на сервер

**Для пользователя с Telegram ID: 602720033**

---

## 📋 Предварительные требования

На сервере должны быть установлены:
- Docker
- Docker Compose
- Git

---

## 🚀 Деплой за 5 минут

### 1. Подключитесь к серверу

```bash
ssh user@your-server.com
```

### 2. Клонируйте репозиторий

```bash
cd /opt
sudo git clone https://github.com/geodez/vending-admin-v2.git
cd vending-admin-v2/backend
```

### 3. Создайте .env файл

```bash
sudo cp .env.example .env
sudo nano .env
```

**Минимальные настройки для старта:**

```env
# Telegram Bot Token (ОБЯЗАТЕЛЬНО!)
TELEGRAM_BOT_TOKEN=ваш_токен_бота_от_@BotFather

# JWT Secret (ОБЯЗАТЕЛЬНО СГЕНЕРИРУЙТЕ НОВЫЙ!)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Остальное можно оставить по умолчанию для теста
```

### 4. Запустите автоматический деплой

```bash
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

Скрипт автоматически:
- ✅ Запустит PostgreSQL и FastAPI
- ✅ Применит миграции БД
- ✅ Создаст вашего пользователя (Owner)
- ✅ Проверит работу API

### 5. Проверьте что всё работает

```bash
curl http://localhost:8000/health
```

Ответ должен быть:
```json
{"status":"healthy"}
```

---

## ✅ Готово!

Ваш Backend запущен:
- **API:** http://your-server:8000
- **API Docs:** http://your-server:8000/docs
- **Health Check:** http://your-server:8000/health

**Ваш User ID:** 602720033  
**Роль:** Owner (полный доступ)

---

## 🔧 Полезные команды

### Посмотреть логи

```bash
cd /opt/vending-admin-v2/backend
sudo docker-compose logs -f app
```

### Перезапустить API

```bash
cd /opt/vending-admin-v2/backend
sudo docker-compose restart app
```

### Остановить всё

```bash
cd /opt/vending-admin-v2/backend
sudo docker-compose down
```

### Запустить заново

```bash
cd /opt/vending-admin-v2/backend
sudo docker-compose up -d
```

### Проверить пользователя в БД

```bash
cd /opt/vending-admin-v2/backend
sudo docker-compose exec db psql -U vending -d vending -c "SELECT * FROM users;"
```

---

## 🌐 Настройка Nginx (опционально)

Если хотите проксировать через Nginx:

```bash
sudo nano /etc/nginx/sites-available/vending-api
```

Содержимое:
```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/vending-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 Получение TELEGRAM_BOT_TOKEN

1. Откройте Telegram
2. Найдите бота [@BotFather](https://t.me/BotFather)
3. Отправьте `/newbot`
4. Следуйте инструкциям
5. Скопируйте токен и вставьте в `.env`

---

## 📝 Следующие шаги

После запуска Backend:
1. ✅ Backend работает на порту 8000
2. ✅ Ваш пользователь создан (602720033)
3. 🔜 Запустить Frontend (React + Telegram Mini App)
4. 🔜 Настроить Telegram Bot для Mini App

---

## 🆘 Помощь

Если что-то не работает:

1. Проверьте логи:
   ```bash
   sudo docker-compose logs app
   ```

2. Проверьте что контейнеры запущены:
   ```bash
   sudo docker-compose ps
   ```

3. Проверьте .env файл:
   ```bash
   cat .env | grep TELEGRAM_BOT_TOKEN
   ```

4. Проверьте доступность порта:
   ```bash
   curl http://localhost:8000/health
   ```

---

**GitHub:** https://github.com/geodez/vending-admin-v2  
**Документация:** См. `backend/DEPLOY.md` для детальных инструкций
