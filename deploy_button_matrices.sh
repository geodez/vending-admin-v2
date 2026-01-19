#!/bin/bash
# Скрипт для деплоя button matrices на сервер vending-prod

set -e

echo "🚀 Деплой Button Matrices на сервер"
echo "===================================="

# 1. Обновление кода на сервере
echo ""
echo "📥 Шаг 1: Обновление кода из GitHub..."
ssh vending-prod "cd /opt/vending-admin-v2 && git pull origin main"

# 2. Проверка наличия миграции
echo ""
echo "🔍 Шаг 2: Проверка миграции..."
if ssh vending-prod "test -f /opt/vending-admin-v2/backend/migrations/versions/0006_create_button_matrices.py"; then
    echo "✅ Миграция 0006 найдена"
else
    echo "❌ Миграция 0006 не найдена! Убедитесь что изменения запушены в репозиторий."
    exit 1
fi

# 3. Пересборка и перезапуск Backend
echo ""
echo "🐳 Шаг 3: Пересборка Backend..."
ssh vending-prod "cd /opt/vending-admin-v2/backend && \
    docker compose down && \
    docker compose build --no-cache && \
    docker compose up -d"

# 4. Ожидание запуска
echo ""
echo "⏳ Шаг 4: Ожидание запуска контейнеров..."
sleep 10

# 5. Применение миграции
echo ""
echo "📦 Шаг 5: Применение миграции 0006..."
ssh vending-prod "cd /opt/vending-admin-v2/backend && \
    docker compose exec -T app alembic upgrade head"

# 6. Проверка миграции
echo ""
echo "✅ Шаг 6: Проверка примененной миграции..."
CURRENT_VERSION=$(ssh vending-prod "cd /opt/vending-admin-v2/backend && docker compose exec -T app alembic current" | grep -oP '0006_[^ ]*' || echo "")
if [ -n "$CURRENT_VERSION" ]; then
    echo "✅ Миграция 0006 применена успешно!"
else
    echo "⚠️  Текущая версия миграции:"
    ssh vending-prod "cd /opt/vending-admin-v2/backend && docker compose exec -T app alembic current"
fi

# 7. Проверка таблиц
echo ""
echo "🔍 Шаг 7: Проверка созданных таблиц..."
ssh vending-prod "cd /opt/vending-admin-v2/backend && docker compose exec -T db psql -U vending -d vending -c \"
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('button_matrices', 'button_matrix_items', 'terminal_matrix_map')
ORDER BY table_name;
\""

# 8. Пересборка Frontend
echo ""
echo "🌐 Шаг 8: Пересборка Frontend..."
ssh vending-prod "cd /opt/vending-admin-v2/frontend && \
    npm ci && \
    npm run build && \
    sudo rm -rf /var/www/vending-admin/* && \
    sudo cp -r dist/* /var/www/vending-admin/ && \
    sudo chown -R www-data:www-data /var/www/vending-admin && \
    sudo chmod -R 755 /var/www/vending-admin"

# 9. Перезапуск Nginx
echo ""
echo "🔄 Шаг 9: Перезапуск Nginx..."
ssh vending-prod "sudo nginx -t && sudo systemctl restart nginx"

# 10. Финальная проверка
echo ""
echo "✅ Шаг 10: Финальная проверка..."
echo ""
echo "📊 Статус контейнеров:"
ssh vending-prod "cd /opt/vending-admin-v2/backend && docker compose ps"

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "📝 Проверьте:"
echo "  - Frontend: https://admin.b2broundtable.ru"
echo "  - API Docs: https://admin.b2broundtable.ru/docs"
echo "  - Новая страница 'Шаблоны матриц' должна быть в меню (только для owner)"
