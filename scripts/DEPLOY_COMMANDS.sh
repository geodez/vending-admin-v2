#!/bin/bash
# Скрипт для деплоя тестовой ветки на сервер
# Использование: ./DEPLOY_COMMANDS.sh

set -e

echo "🚀 Деплой тестовой ветки на сервер"
echo ""

# 1. Push ветки на GitHub
echo "📤 Push ветки на GitHub..."
git push origin test/improvement-plan-implementation

echo ""
echo "✅ Ветка отправлена на GitHub"
echo ""
echo "📋 Следующие шаги на сервере:"
echo ""
echo "1. Подключиться к серверу:"
echo "   ssh vending-prod"
echo ""
echo "2. Выполнить команды:"
echo "   cd /opt/vending-admin-v2"
echo "   git fetch origin"
echo "   git checkout test/improvement-plan-implementation"
echo "   cd backend"
echo "   docker compose -f docker-compose.prod.yml up -d --build app"
echo "   cd ../frontend"
echo "   npm ci && npm run build"
echo ""
echo "3. Проверить статус:"
echo "   cd backend"
echo "   docker compose -f docker-compose.prod.yml ps"
echo "   docker compose -f docker-compose.prod.yml logs app --tail=50"
echo ""
echo "4. Запустить тесты:"
echo "   cd /opt/vending-admin-v2"
echo "   ./test_new_endpoints.sh <JWT_TOKEN>"
echo ""
echo "📝 Подробные инструкции в DEPLOY_TEST_BRANCH.md"
