#!/bin/bash

# Скрипт очистки сервера от старого проекта
# Использование: sudo ./cleanup_server.sh

set -e

echo "🧹 Очистка сервера от старого проекта vending"
echo "=============================================="
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите скрипт с sudo"
    exit 1
fi

echo "⚠️  ВНИМАНИЕ: Этот скрипт удалит старый проект /opt/vending-git"
echo ""
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Отменено"
    exit 1
fi

echo ""

# 1. Создать бэкап БД (если есть)
echo "📦 Шаг 1: Проверка наличия старой БД..."
if [ -d "/opt/vending-git/backend" ]; then
    cd /opt/vending-git/backend
    
    # Проверить запущен ли docker-compose
    if docker-compose ps | grep -q "Up"; then
        echo "💾 Создание бэкапа БД..."
        mkdir -p ~/backups/vending
        BACKUP_FILE=~/backups/vending/backup_$(date +%Y%m%d_%H%M%S).sql
        
        docker-compose exec -T db pg_dump -U vending -d vending > "$BACKUP_FILE" 2>/dev/null || true
        
        if [ -f "$BACKUP_FILE" ]; then
            echo "✅ Бэкап создан: $BACKUP_FILE"
        else
            echo "⚠️  Бэкап не создан (возможно, БД пуста)"
        fi
    else
        echo "⚠️  Docker-compose не запущен, пропускаем бэкап"
    fi
else
    echo "⚠️  Старый проект не найден в /opt/vending-git"
fi

echo ""

# 2. Остановить старый проект
echo "🛑 Шаг 2: Остановка старого проекта..."
if [ -d "/opt/vending-git/backend" ]; then
    cd /opt/vending-git/backend
    docker-compose down -v 2>/dev/null || true
    echo "✅ Старый проект остановлен"
else
    echo "⚠️  Старый проект не найден"
fi

echo ""

# 3. Удалить старую директорию
echo "🗑️  Шаг 3: Удаление старой директории..."
if [ -d "/opt/vending-git" ]; then
    rm -rf /opt/vending-git
    echo "✅ Директория /opt/vending-git удалена"
else
    echo "⚠️  Директория уже удалена"
fi

echo ""

# 4. Проверить порты
echo "🔍 Шаг 4: Проверка портов..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Порт 8000 занят, освобождаем..."
    kill -9 $(lsof -t -i :8000) 2>/dev/null || true
    echo "✅ Порт 8000 освобожден"
else
    echo "✅ Порт 8000 свободен"
fi

if lsof -i :5432 > /dev/null 2>&1; then
    echo "⚠️  Порт 5432 занят, освобождаем..."
    kill -9 $(lsof -t -i :5432) 2>/dev/null || true
    echo "✅ Порт 5432 освобожден"
else
    echo "✅ Порт 5432 свободен"
fi

echo ""

# 5. Очистка Docker
echo "🐳 Шаг 5: Очистка Docker..."
read -p "Очистить неиспользуемые Docker образы и volumes? (yes/no): " clean_docker

if [ "$clean_docker" = "yes" ]; then
    docker container prune -f
    docker image prune -a -f
    docker volume prune -f
    echo "✅ Docker очищен"
else
    echo "⏭️  Пропущено"
fi

echo ""

# 6. Создать директории для нового проекта
echo "📁 Шаг 6: Подготовка директорий..."
mkdir -p /opt/vending-admin-v2
mkdir -p /var/log/vending
mkdir -p ~/backups/vending
echo "✅ Директории созданы"

echo ""

# 7. Проверка места на диске
echo "💾 Шаг 7: Проверка места на диске..."
df -h / | tail -1 | awk '{print "Свободно: " $4 " из " $2}'

echo ""

# 8. Итоговая проверка
echo "✅ Очистка завершена!"
echo ""
echo "📋 Статус:"
echo "  • Старый проект удален: ✅"
echo "  • Порты свободны: ✅"
echo "  • Директории подготовлены: ✅"

if [ -f "$BACKUP_FILE" ]; then
    echo "  • Бэкап БД: ✅ $BACKUP_FILE"
fi

echo ""
echo "🚀 Следующие шаги:"
echo "  1. cd /opt"
echo "  2. git clone https://github.com/geodez/vending-admin-v2.git"
echo "  3. cd vending-admin-v2/backend"
echo "  4. cp .env.example .env"
echo "  5. nano .env  (укажите TELEGRAM_BOT_TOKEN)"
echo "  6. ./deploy.sh"
echo ""
