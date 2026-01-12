# 🚀 Деплой Backend на сервер

## Вариант 1: Через Docker Compose (рекомендуется)

### На сервере выполните:

```bash
# 1. Клонировать репозиторий
cd /opt
git clone https://github.com/geodez/vending-admin-v2.git
cd vending-admin-v2/backend

# 2. Создать .env файл
cp .env.example .env
nano .env
```

### В .env укажите:

```env
# Database
DATABASE_URL=postgresql://vending:vending_pass@db:5432/vending

# JWT (ОБЯЗАТЕЛЬНО СМЕНИТЕ!)
SECRET_KEY=ваш-длинный-случайный-секретный-ключ-минимум-32-символа
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# Telegram (ОБЯЗАТЕЛЬНО!)
TELEGRAM_BOT_TOKEN=ваш-реальный-токен-бота

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS (добавьте ваш домен)
CORS_ORIGINS=https://your-domain.com,http://localhost:5173
```

### 3. Запустить Docker Compose

```bash
docker-compose up -d
```

### 4. Применить миграции

```bash
docker-compose exec app alembic upgrade head
```

### 5. Создать первого пользователя (Owner)

**Ваш Telegram User ID: 602720033**

```bash
docker-compose exec db psql -U vending -d vending -c "
INSERT INTO users (telegram_user_id, username, first_name, role, is_active)
VALUES (602720033, 'owner', 'Owner', 'owner', true);
"
```

### 6. Проверить что API работает

```bash
curl http://localhost:8000/health
```

Ответ должен быть:
```json
{"status":"healthy"}
```

---

## Вариант 2: Без Docker (systemd)

### 1. Установить зависимости

```bash
# PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib python3-pip python3-venv

# Создать БД
sudo -u postgres psql
CREATE DATABASE vending;
CREATE USER vending WITH PASSWORD 'vending_pass';
GRANT ALL PRIVILEGES ON DATABASE vending TO vending;
\q
```

### 2. Настроить проект

```bash
cd /opt/vending-admin-v2/backend

# Создать venv
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env
cp .env.example .env
nano .env
```

В .env измените:
```env
DATABASE_URL=postgresql://vending:vending_pass@localhost:5432/vending
TELEGRAM_BOT_TOKEN=ваш-токен
SECRET_KEY=ваш-секретный-ключ
```

### 3. Применить миграции

```bash
source venv/bin/activate
alembic upgrade head
```

### 4. Создать systemd сервис

```bash
sudo nano /etc/systemd/system/vending-api.service
```

Содержимое:
```ini
[Unit]
Description=Vending Admin API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/vending-admin-v2/backend
Environment="PATH=/opt/vending-admin-v2/backend/venv/bin"
ExecStart=/opt/vending-admin-v2/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Запустить сервис

```bash
sudo systemctl daemon-reload
sudo systemctl enable vending-api
sudo systemctl start vending-api
sudo systemctl status vending-api
```

### 6. Создать пользователя

```bash
sudo -u postgres psql -d vending -c "
INSERT INTO users (telegram_user_id, username, first_name, role, is_active)
VALUES (602720033, 'owner', 'Owner', 'owner', true);
"
```

---

## 🌐 Настройка Nginx (reverse proxy)

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
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
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

### SSL с Certbot

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.com
```

---

## 🔐 Генерация SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

Или через командную строку:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📝 Полезные команды

### Логи (Docker)
```bash
docker-compose logs -f app
```

### Логи (systemd)
```bash
sudo journalctl -u vending-api -f
```

### Перезапуск
```bash
# Docker
docker-compose restart app

# systemd
sudo systemctl restart vending-api
```

### Проверка БД
```bash
# Docker
docker-compose exec db psql -U vending -d vending

# Локально
sudo -u postgres psql -d vending

# Посмотреть пользователей
SELECT * FROM users;
```

---

## 🐛 Troubleshooting

### API не отвечает

1. Проверить что сервис запущен:
```bash
# Docker
docker-compose ps

# systemd
sudo systemctl status vending-api
```

2. Проверить логи:
```bash
# Docker
docker-compose logs app

# systemd
sudo journalctl -u vending-api -n 100
```

### База данных не подключается

1. Проверить что PostgreSQL запущен:
```bash
sudo systemctl status postgresql
```

2. Проверить что БД создана:
```bash
sudo -u postgres psql -l | grep vending
```

### Telegram auth не работает

1. Проверить что `TELEGRAM_BOT_TOKEN` указан правильно в `.env`
2. Проверить что в БД есть пользователь с вашим `telegram_user_id`

---

## ✅ Чек-лист деплоя

- [ ] Клонирован репозиторий
- [ ] Создан `.env` с реальными данными
- [ ] Запущен PostgreSQL
- [ ] Применены миграции
- [ ] Создан пользователь (telegram_user_id: 602720033)
- [ ] API отвечает на /health
- [ ] Настроен Nginx (опционально)
- [ ] Настроен SSL (опционально)

---

**Ваш Telegram User ID для первого пользователя: `602720033`**

После деплоя API будет доступен по адресу:
- Локально: `http://localhost:8000`
- С Nginx: `https://api.your-domain.com`

API документация:
- Swagger UI: `http://your-domain:8000/docs`
- ReDoc: `http://your-domain:8000/redoc`
