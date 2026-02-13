#!/bin/bash
# Manual deployment script for hot-fixing production

set -e

SERVER="vend@192.168.1.104"
APP_DIR="~/app"

echo "Step 1: Fixing environment configuration..."
ssh $SERVER "cd $APP_DIR && ln -sf .env.prod .env"

echo "Step 2: Copying dependencies..."
ssh $SERVER "mkdir -p $APP_DIR/backend/pkgs"
scp backend/pkgs/*.whl $SERVER:$APP_DIR/backend/pkgs/

echo "Step 3: Updating docker-compose..."
scp docker-compose.prod.yml $SERVER:$APP_DIR/

echo "Step 4: Restarting application..."
# Force recreate ensures new volume mounts and env vars are picked up
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml up -d --force-recreate app"

echo "Deployment complete! Checking logs..."
ssh $SERVER "cd $APP_DIR && docker compose -f docker-compose.prod.yml logs --tail=50 -f app"
