# 🚀 КОМАНДЫ ДЛЯ ОБНОВЛЕНИЯ СЕРВЕРА

Выполните эти команды **последовательно** на вашем сервере для применения последних исправлений.

---

## 🔄 **ШАГ 1: Обновление кода из GitHub**

```bash
cd /opt/vending-admin-v2
sudo git pull origin main
```

Должно показать:
```
Updating b9dece2..ba4a8af
Fast-forward
 DEPLOYMENT_FINAL_STEPS.md        | 185 ++++++++++++++++++++++++++++++++++++++
 backend/app/main.py              |   3 +-
 backend/docker-compose.prod.yml  |   2 -
 backend/docker-compose.yml       |   2 -
 4 files changed, 190 insertions(+), 5 deletions(-)
```

---

## 🐳 **ШАГ 2: Пересборка Backend (Docker)**

```bash
cd /opt/vending-admin-v2/backend
sudo docker compose down
sudo docker compose build --no-cache
sudo docker compose up -d
```

⏱️ **Займёт 2-3 минуты (сборка образа + запуск)**

Проверка:
```bash
sudo docker compose ps
```

Должно показать:
```
NAME              STATUS         PORTS
backend-app-1     Up (healthy)   0.0.0.0:8000->8000/tcp
backend-db-1      Up (healthy)   0.0.0.0:5432->5432/tcp
```

---

## 🌐 **ШАГ 3: Пересборка Frontend**

```bash
cd /opt/vending-admin-v2/frontend
npm run build
sudo rm -rf /var/www/vending-admin/*
sudo cp -r dist/* /var/www/vending-admin/
sudo chown -R www-data:www-data /var/www/vending-admin
sudo chmod -R 755 /var/www/vending-admin
```

---

## 🔄 **ШАГ 4: Перезапуск Nginx**

```bash
sudo nginx -t
sudo systemctl restart nginx
```

Должно показать:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## ✅ **ШАГ 5: Проверка работы**

### A) Проверка Backend API:
```bash
curl https://admin.b2broundtable.ru/health
```

Ожидаемый результат:
```json
{"status":"healthy"}
```

### B) Проверка API Documentation:
```bash
curl -I https://admin.b2broundtable.ru/docs
```

Должно показать `200 OK`

### C) Проверка Users API (новый endpoint):
```bash
curl https://admin.b2broundtable.ru/api/v1/users
```

Должно показать `401 Unauthorized` (это нормально - требуется авторизация)

---

## 🔍 **ШАГ 6: Проверка логов Backend**

```bash
cd /opt/vending-admin-v2/backend
sudo docker compose logs -f app
```

Логи должны показывать:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Нажмите **Ctrl+C** чтобы выйти из логов.

---

## 🎯 **ШАГ 7: Тест входа через Telegram**

1. Откройте Telegram
2. Найдите вашего бота
3. Нажмите кнопку **Menu** (внизу)
4. Выберите **Admin Panel** (или как вы её назвали)
5. Нажмите **"Войти через Telegram"**

В логах на сервере (`sudo docker compose logs -f app`) вы должны увидеть:
```
INFO:     POST /api/v1/auth/telegram
INFO:     User authenticated: 602720033
```

---

## ✅ **Что было исправлено:**

1. ✅ Удалён устаревший атрибут `version` из `docker-compose.yml` и `docker-compose.prod.yml`
2. ✅ Добавлен **Users router** в `main.py` (API для управления пользователями)
3. ✅ Создана документация для деплоя (`DEPLOYMENT_FINAL_STEPS.md`)

---

## 🐛 **Если что-то не работает:**

### Backend не стартует:
```bash
cd /opt/vending-admin-v2/backend
sudo docker compose logs app
```

### Frontend показывает ошибки:
```bash
sudo tail -f /var/log/nginx/error.log
```

### Docker проблемы:
```bash
# Полная очистка и перезапуск
cd /opt/vending-admin-v2/backend
sudo docker compose down -v
sudo docker compose up -d --build
```

---

## 📊 **Проверка статуса всех сервисов:**

```bash
# Docker контейнеры
sudo docker ps

# Nginx
sudo systemctl status nginx

# Порты
sudo netstat -tulpn | grep -E ':(80|443|5432|8000)'
```

---

## 🎉 **После выполнения всех команд:**

✅ Backend обновлён с новыми исправлениями  
✅ Frontend пересобран  
✅ Nginx перезапущен  
✅ API endpoints доступны  
✅ Telegram Mini App работает  

---

## 📝 **Полезные команды для мониторинга:**

```bash
# Логи Backend в реальном времени
cd /opt/vending-admin-v2/backend && sudo docker compose logs -f app

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Статус Docker контейнеров
sudo docker ps -a

# Перезапуск всего (если нужно)
cd /opt/vending-admin-v2/backend
sudo docker compose restart
sudo systemctl restart nginx
```

---

🚀 **Готово! Ваш проект обновлён и готов к использованию!**
