#!/bin/bash
# Скрипт для развертывания из GitHub на Proxmox сервер

set -e  # Остановка при ошибке

echo "🚀 Deploying from GitHub to Proxmox server..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Параметры
SERVER="vend@192.168.1.104"
APP_DIR="~/app"
BRANCH="${1:-main}"  # По умолчанию main, но можно указать другую ветку

echo -e "${YELLOW}Deploying branch: $BRANCH${NC}"
echo ""

echo -e "${YELLOW}Step 1: Stopping containers...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml down"

echo -e "${YELLOW}Step 2: Backing up current state...${NC}"
ssh $SERVER "cd $APP_DIR && tar -czf ~/backup-before-deploy-\$(date +%Y%m%d-%H%M%S).tar.gz --exclude='node_modules' --exclude='__pycache__' --exclude='postgres_data' --exclude='.git' --exclude='logs' ."

echo -e "${YELLOW}Step 3: Backing up .env.prod file...${NC}"
ssh $SERVER "cp $APP_DIR/.env.prod /tmp/env.prod.backup"

echo -e "${YELLOW}Step 4: Backing up postgres_data...${NC}"
ssh $SERVER "if [ -d $APP_DIR/postgres_data ]; then mv $APP_DIR/postgres_data /tmp/postgres_data_backup; fi"

echo -e "${YELLOW}Step 5: Removing old code...${NC}"
ssh $SERVER "cd $APP_DIR && find . -mindepth 1 -maxdepth 1 ! -name 'postgres_data' ! -name '.env.prod' -exec rm -rf {} +"

echo -e "${YELLOW}Step 6: Cloning repository from GitHub...${NC}"
# Клонируем во временную директорию на локальной машине
TEMP_DIR=$(mktemp -d)
echo "Cloning to temporary directory: $TEMP_DIR"
git clone -b $BRANCH https://github.com/geodez/vending-admin-v2.git "$TEMP_DIR"

echo -e "${YELLOW}Step 7: Copying files to server...${NC}"
rsync -av --exclude='.git' --exclude='node_modules' --exclude='__pycache__' --exclude='postgres_data' --exclude='.env' --exclude='logs' "$TEMP_DIR/" $SERVER:$APP_DIR/

echo -e "${YELLOW}Step 8: Cleaning up temporary directory...${NC}"
rm -rf "$TEMP_DIR"

echo -e "${YELLOW}Step 9: Restoring .env.prod file...${NC}"
ssh $SERVER "cp /tmp/env.prod.backup $APP_DIR/.env.prod"

echo -e "${YELLOW}Step 10: Restoring postgres_data...${NC}"
ssh $SERVER "if [ -d /tmp/postgres_data_backup ]; then mv /tmp/postgres_data_backup $APP_DIR/postgres_data; fi"

echo -e "${YELLOW}Step 11: Building and starting containers...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d --build"

echo -e "${YELLOW}Step 12: Waiting for containers to start...${NC}"
sleep 15

echo -e "${YELLOW}Step 13: Running database migrations...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml exec -T app alembic upgrade head"

echo -e "${YELLOW}Step 14: Checking container status...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml ps"

echo -e "${YELLOW}Step 15: Checking backend logs...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml logs --tail=50 app"

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Test the application at https://romanrazdobreev.store"
echo "2. Check logs: ssh $SERVER 'cd $APP_DIR && docker compose -f docker-compose.prod.yml logs -f'"
echo "3. If needed, rollback: ssh $SERVER 'cd ~ && ls -lt backup-*.tar.gz | head -1'"
echo ""
echo "📚 Backups created:"
ssh $SERVER "ls -lht ~/backup-*.tar.gz | head -3"
