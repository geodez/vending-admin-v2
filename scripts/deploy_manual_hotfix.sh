#!/bin/bash
# Manual deployment script for hot-fixing production

set -e

SERVER="vend@192.168.1.104"
APP_DIR="~/app"

echo "Step 0: Building Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
npm run build
cd ..

echo "Step 1: Fixing environment configuration..."
ssh $SERVER "cd $APP_DIR && ln -sf .env.prod .env"

echo "Step 2: Copying dependencies and code..."
ssh $SERVER "mkdir -p $APP_DIR/backend/pkgs $APP_DIR/backend/migrations $APP_DIR/frontend_dist"
scp backend/pkgs/*.whl $SERVER:$APP_DIR/backend/pkgs/
scp -r backend/migrations $SERVER:$APP_DIR/backend/
scp -r backend/app $SERVER:$APP_DIR/backend/
scp backend/alembic.ini $SERVER:$APP_DIR/backend/
scp -r frontend/dist/* $SERVER:$APP_DIR/frontend_dist/

echo "Step 3: Updating docker-compose..."
scp docker-compose.prod.yml $SERVER:$APP_DIR/

echo "Step 4: Restarting application..."
# Force recreate ensures new volume mounts and env vars are picked up
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d --force-recreate app frontend"

echo "Deployment complete! Checking logs..."
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml logs --tail=50 -f app"
