#!/bin/bash
# Скрипт для развертывания изменений авторизации на Proxmox сервер через SCP

set -e  # Остановка при ошибке

echo "🚀 Deploying authentication changes to Proxmox server..."

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Параметры
SERVER="vend@192.168.1.104"
APP_DIR="~/app"

echo -e "${YELLOW}Step 1: Copying backend files...${NC}"
scp backend/app/models/user.py $SERVER:$APP_DIR/backend/app/models/
scp backend/app/schemas/auth.py $SERVER:$APP_DIR/backend/app/schemas/
scp backend/app/crud/user.py $SERVER:$APP_DIR/backend/app/crud/
scp backend/app/api/v1/auth.py $SERVER:$APP_DIR/backend/app/api/v1/
scp backend/requirements.txt $SERVER:$APP_DIR/backend/

echo -e "${YELLOW}Step 2: Creating backend/app/auth directory and copying password.py...${NC}"
ssh $SERVER "mkdir -p $APP_DIR/backend/app/auth"
scp backend/app/auth/password.py $SERVER:$APP_DIR/backend/app/auth/

echo -e "${YELLOW}Step 3: Creating backend/scripts directory and copying create_user.py...${NC}"
ssh $SERVER "mkdir -p $APP_DIR/backend/scripts"
scp backend/scripts/create_user.py $SERVER:$APP_DIR/backend/scripts/

echo -e "${YELLOW}Step 4: Copying migration file...${NC}"
scp backend/migrations/versions/0009_add_email_password_auth.py $SERVER:$APP_DIR/backend/migrations/versions/

echo -e "${YELLOW}Step 5: Copying frontend files...${NC}"
scp frontend/src/pages/LoginPage.tsx $SERVER:$APP_DIR/frontend/src/pages/
scp frontend/src/api/auth.ts $SERVER:$APP_DIR/frontend/src/api/
scp frontend/src/types/api.ts $SERVER:$APP_DIR/frontend/src/types/

echo -e "${YELLOW}Step 6: Copying documentation...${NC}"
ssh $SERVER "mkdir -p $APP_DIR/docs"
scp docs/AUTHENTICATION.md $SERVER:$APP_DIR/docs/
scp docs/TELEGRAM_BOT_SETUP.md $SERVER:$APP_DIR/docs/
scp docs/CHANGES_AUTH_2026-02-13.md $SERVER:$APP_DIR/docs/
scp QUICK_START_TELEGRAM.md $SERVER:$APP_DIR/

echo -e "${YELLOW}Step 7: Installing backend dependencies...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml exec -T backend pip install passlib[bcrypt]"

echo -e "${YELLOW}Step 8: Running database migration...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"

echo -e "${YELLOW}Step 9: Rebuilding and restarting containers...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d --build"

echo -e "${YELLOW}Step 10: Waiting for containers to start...${NC}"
sleep 10

echo -e "${YELLOW}Step 11: Checking container status...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml ps"

echo -e "${YELLOW}Step 12: Checking backend logs...${NC}"
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml logs --tail=30 backend"

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📝 Next steps:"
echo "1. Test the application at https://romanrazdobreev.store"
echo "2. Create a test user:"
echo "   ssh $SERVER 'cd $APP_DIR && docker-compose -f docker-compose.prod.yml exec backend python scripts/create_user.py admin@example.com TestPass123 owner Admin'"
echo "3. Configure Telegram bot domain in BotFather: romanrazdobreev.store"
echo ""
echo "📚 Documentation:"
echo "- docs/AUTHENTICATION.md - Full authentication guide"
echo "- docs/TELEGRAM_BOT_SETUP.md - Telegram bot setup"
echo "- QUICK_START_TELEGRAM.md - Quick start guide"
