# Деплой тестовой ветки на сервер

**Ветка:** `test/improvement-plan-implementation`  
**Дата:** 2026-01-25

---

## 📋 Команды для деплоя

### 1. Push ветки на GitHub

```bash
# Локально
git push origin test/improvement-plan-implementation
```

### 2. Деплой на сервер vending-prod

```bash
# Подключиться к серверу
ssh vending-prod

# Перейти в директорию проекта
cd /opt/vending-admin-v2

# Получить обновления
git fetch origin

# Переключиться на тестовую ветку
git checkout test/improvement-plan-implementation

# Обновить backend
cd backend
docker compose -f docker-compose.prod.yml up -d --build app

# Проверить статус
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs app --tail=50

# Обновить frontend
cd ../frontend
npm ci
npm run build

# Проверить, что build прошел успешно
ls -la dist/

# Скопировать в nginx (если нужно)
# cp -r dist/* /var/www/vending-admin/
# systemctl reload nginx
```

---

## 🧪 Тестирование после деплоя

### 1. Проверка здоровья приложения

```bash
curl http://localhost:8000/health
```

### 2. Получение JWT токена

Через браузер:
1. Открыть приложение
2. Авторизоваться
3. В DevTools → Application → Local Storage → найти `access_token`
4. Скопировать токен

### 3. Запуск тестового скрипта

```bash
# На сервере
cd /opt/vending-admin-v2
chmod +x test_new_endpoints.sh
./test_new_endpoints.sh <JWT_TOKEN>
```

### 4. Проверка логов

```bash
# Backend логи
cd /opt/vending-admin-v2/backend
docker compose -f docker-compose.prod.yml logs app --tail=100 -f

# Nginx логи (если нужно)
tail -f /var/log/nginx/error.log
```

---

## ✅ Чеклист тестирования

### Backend endpoints

- [ ] GET `/api/v1/analytics/sales/summary` - работает
- [ ] GET `/api/v1/analytics/sales/margin` - работает
- [ ] GET `/api/v1/analytics/owner-report/daily` - работает
- [ ] GET `/api/v1/analytics/owner-report/issues` - работает
- [ ] GET `/api/v1/expenses/analytics` - работает
- [ ] GET `/api/v1/expenses/categories` - работает
- [ ] POST `/api/v1/mapping/button-matrices/{id}/items/batch` - работает
- [ ] POST `/api/v1/mapping/button-matrices/{id}/clone` - работает

### Существующие endpoints (регрессия)

- [ ] GET `/api/v1/analytics/overview` - работает
- [ ] GET `/api/v1/mapping/button-matrices` - работает
- [ ] GET `/api/v1/expenses/` - работает

### Frontend

- [ ] Приложение открывается
- [ ] Нет ошибок в консоли браузера
- [ ] API запросы работают корректно

---

## 🔄 После успешного тестирования

### Вариант 1: Merge в main

```bash
# Локально
git checkout main
git merge test/improvement-plan-implementation
git push origin main

# На сервере
cd /opt/vending-admin-v2
git checkout main
git pull origin main
cd backend
docker compose -f docker-compose.prod.yml up -d --build app
cd ../frontend
npm ci && npm run build
```

### Вариант 2: Откат (если что-то не работает)

```bash
# На сервере
cd /opt/vending-admin-v2
git checkout main
cd backend
docker compose -f docker-compose.prod.yml up -d --build app
cd ../frontend
npm ci && npm run build
```

---

## 📝 Примечания

- Тестовая ветка создана для безопасного тестирования
- После успешного тестирования можно смержить в main
- При проблемах можно легко откатиться на main

---

**Готово к деплою!** ✅
