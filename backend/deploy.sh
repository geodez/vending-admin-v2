#!/bin/bash

# Скрипт автоматического деплоя Backend
# Использование: ./deploy.sh

set -e  # Остановка при ошибке

echo "🚀 Деплой Vending Admin v2 Backend"
echo "=================================="

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose не установлен"
    exit 1
fi

# Определяем команду docker compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "✅ Docker найден"

# Проверка .env
if [ ! -f ".env" ]; then
    echo "⚠️  .env файл не найден, создаем из .env.example"
    cp .env.example .env
    echo "📝 Отредактируйте .env файл и запустите скрипт снова"
    exit 1
fi

echo "✅ .env файл найден"

# Проверка TELEGRAM_BOT_TOKEN
if grep -q "your-bot-token-here" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN не настроен в .env"
    echo "📝 Отредактируйте .env файл и укажите реальный токен бота"
    exit 1
fi

echo "✅ TELEGRAM_BOT_TOKEN настроен"

# Остановка старых контейнеров
echo ""
echo "🛑 Остановка старых контейнеров..."
$DOCKER_COMPOSE down || true

# Сборка и запуск
echo ""
echo "🏗️  Сборка и запуск контейнеров..."
$DOCKER_COMPOSE up -d --build

# Ожидание запуска БД
echo ""
echo "⏳ Ожидание запуска PostgreSQL..."
sleep 10

# Применение миграций
echo ""
echo "📦 Применение миграций..."
$DOCKER_COMPOSE exec -T app alembic upgrade head

# Создание пользователя
echo ""
echo "👤 Создание пользователя (Owner)..."
$DOCKER_COMPOSE exec -T db psql -U vending -d vending < create_owner.sql

# Проверка здоровья API
echo ""
echo "🔍 Проверка API..."
sleep 3

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API работает!"
else
    echo "⚠️  API не отвечает, проверьте логи: $DOCKER_COMPOSE logs app"
fi

# Показываем статус
echo ""
echo "📊 Статус контейнеров:"
$DOCKER_COMPOSE ps

echo ""
echo "✅ Деплой завершен!"
echo ""
echo "📝 Полезные команды:"
echo "  - Логи:       $DOCKER_COMPOSE logs -f app"
echo "  - Перезапуск: $DOCKER_COMPOSE restart app"
echo "  - Остановка:  $DOCKER_COMPOSE down"
echo ""
echo "🌐 API доступен:"
echo "  - Health:     http://localhost:8000/health"
echo "  - API Docs:   http://localhost:8000/docs"
echo "  - ReDoc:      http://localhost:8000/redoc"
echo ""
echo "👤 Ваш User ID: 602720033"
echo ""
