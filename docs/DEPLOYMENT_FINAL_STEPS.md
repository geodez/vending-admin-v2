# 🚀 Финальные шаги для деплоя на сервере

После всех исправлений в коде выполните следующие команды на сервере:

---

## 🚨 ВАЖНО: Если Docker Hub недоступен

Используйте скрипт ручного обновления (Hotfix):
```bash
./scripts/deploy_manual_hotfix.sh
```
Подробнее см. в [AUTHENTICATION.md](./AUTHENTICATION.md#настройка-и-развертывание-production).

---

## 📋 **Обновление кода на сервере**

```bash
# Переход в директорию проекта
cd /opt/vending-admin-v2

# Получение последних изменений из GitHub
sudo git pull origin main

# Переход в backend
cd backend
```

---

## 🔧 **Пересборка и перезапуск Backend**

```bash
# Остановка контейнеров
sudo docker compose down

# Пересборка образов (важно после изменений в коде!)
sudo docker compose build --no-cache

# Запуск контейнеров
sudo docker compose up -d

# Проверка логов
sudo docker compose logs -f app
```

Нажмите **Ctrl+C** чтобы выйти из логов.

---

## 🌐 **Пересборка Frontend**

```bash
# Переход в frontend
cd /opt/vending-admin-v2/frontend

# Пересборка с production настройками
npm run build

# Копирование новых файлов в Nginx
sudo rm -rf /var/www/vending-admin/*
sudo cp -r dist/* /var/www/vending-admin/

# Проверка прав доступа
sudo chown -R www-data:www-data /var/www/vending-admin
sudo chmod -R 755 /var/www/vending-admin
```

---

## 🔄 **Перезапуск Nginx**

```bash
# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx

# Проверка статуса
sudo systemctl status nginx
```

---

## ✅ **Финальная проверка**

### 1. **Backend API:**
```bash
curl https://admin.b2broundtable.ru/health
```

Должно вернуть:
```json
{"status":"healthy"}
```

### 2. **API Documentation:**

Откройте в браузере:
- **Swagger UI:** https://admin.b2broundtable.ru/docs
- **ReDoc:** https://admin.b2broundtable.ru/redoc

### 3. **Frontend:**

Откройте в Telegram:
- Найдите вашего бота
- Нажмите кнопку **Menu** (внизу у поля ввода)
- Выберите **Admin Panel**
- Должна открыться страница входа

### 4. **Логи Backend (в реальном времени):**
```bash
cd /opt/vending-admin-v2/backend
sudo docker compose logs -f app
```

Теперь попробуйте войти через Telegram - вы увидите логи аутентификации в реальном времени.

---

## 🐛 **Устранение проблем**

### Если Backend не стартует:
```bash
cd /opt/vending-admin-v2/backend
sudo docker compose logs app
```

### Если Frontend показывает ошибки:
```bash
# Проверьте логи Nginx
sudo tail -f /var/log/nginx/error.log
```

### Если Docker контейнеры не стартуют:
```bash
# Полная очистка и перезапуск
cd /opt/vending-admin-v2/backend
sudo docker compose down -v
sudo docker compose up -d --build
```

---

## 📊 **Проверка всех сервисов**

```bash
# Статус Docker контейнеров
sudo docker ps

# Статус Nginx
sudo systemctl status nginx

# Проверка портов
sudo netstat -tulpn | grep -E ':(80|443|5432|8000)'
```

Должно показать:
- `:80` и `:443` - Nginx
- `:5432` - PostgreSQL
- `:8000` - FastAPI (внутри Docker)

---

## 🎉 **Готово!**

После выполнения всех шагов:

1. ✅ Backend API работает на https://admin.b2broundtable.ru
2. ✅ Frontend доступен через Telegram Mini App
3. ✅ База данных настроена и мигрирована
4. ✅ SSL сертификат установлен
5. ✅ Nginx проксирует запросы
6. ✅ Все API endpoints доступны через /docs

---

## 🔐 **Важные файлы и пути на сервере**

- **Проект:** `/opt/vending-admin-v2`
- **Backend код:** `/opt/vending-admin-v2/backend`
- **Frontend файлы:** `/var/www/vending-admin`
- **Nginx конфиг:** `/etc/nginx/sites-available/vending-admin`
- **SSL сертификаты:** `/etc/letsencrypt/live/admin.b2broundtable.ru/`
- **Логи Nginx:** `/var/log/nginx/`
- **Docker логи:** `cd /opt/vending-admin-v2/backend && sudo docker compose logs`

---

## 📞 **Поддержка**

Если что-то не работает:
1. Проверьте логи Backend: `sudo docker compose logs app`
2. Проверьте логи Nginx: `sudo tail -f /var/log/nginx/error.log`
3. Проверьте статус сервисов: `sudo systemctl status nginx`
4. Убедитесь что все контейнеры запущены: `sudo docker ps`
