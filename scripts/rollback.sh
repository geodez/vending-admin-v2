#!/bin/bash
echo "=== Rolling back to previous version ==="
cd /opt/vending-admin-v2
git reset --hard HEAD~1
echo "=== Rebuilding backend ==="
cd backend && docker compose up -d --build
echo "=== Rebuilding frontend ==="
cd ../frontend && npm run build && rm -rf /var/www/vending-admin/* && cp -r dist/* /var/www/vending-admin/
echo "=== Reloading nginx ==="
systemctl reload nginx
echo "✅ Rollback completed!"
