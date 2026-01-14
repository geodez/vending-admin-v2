# 🚀 Quick Start - Telegram OAuth Implementation

Быстрый старт Telegram OAuth авторизации.

## 5 Минут До Готовности

### 1. Get Telegram Bot (30 сек)

1. Open [@BotFather](https://t.me/botfather) in Telegram
2. `/newbot` → follow prompts
3. Копируйте **TOKEN** и **USERNAME**

```
TOKEN=5893214567:ABCDEfghijKLMNop_qrstUVWxyz1234567
USERNAME=your_bot_username
```

### 2. Backend Configuration (1 мин)

```bash
cd backend

# Update .env
nano .env
# TELEGRAM_BOT_TOKEN=<your TOKEN>
# TELEGRAM_BOT_USERNAME=<your USERNAME>

# Or use sed
sed -i 's/your_bot_token_here/<TOKEN>/g' .env
sed -i 's/your_bot_username/<USERNAME>/g' .env
```

### 3. Frontend Configuration (30 сек)

```bash
cd frontend

# Create .env if not exists
cat > .env << EOF
VITE_API_BASE_URL=/api/v1
VITE_TELEGRAM_BOT_USERNAME=<your USERNAME>
EOF
```

### 4. Database User (1 мин)

```sql
-- SSH to your server and run:
psql -U vending -d vending << EOF
INSERT INTO users (telegram_user_id, first_name, role, is_active)
VALUES (YOUR_TELEGRAM_ID, 'Your Name', 'owner', true);
EOF
```

**Get YOUR_TELEGRAM_ID:**
- Open [@getmyidbot](https://t.me/getmyidbot)
- It replies with your ID

### 5. Start Services (1.5 мин)

```bash
# Terminal 1: Backend
cd backend
docker compose up -d --build
# Wait for: "Application startup complete"

# Terminal 2: Frontend
cd frontend
npm install  # (skip if already done)
npm run dev
# Open: http://localhost:5173/login
```

---

## Test It! 🎯

1. Open http://localhost:5173/login
2. Click **"Войти через Telegram"** button
3. Authorize in Telegram
4. → Should redirect to /overview ✅

---

## Troubleshooting 🔧

| Issue | Fix |
|-------|-----|
| 401 Error | Check TELEGRAM_BOT_TOKEN is correct |
| 403 "Доступ запрещен" | Add yourself to DB (see step 4) |
| Widget not showing | Check TELEGRAM_BOT_USERNAME in .env |
| Cannot connect to API | Check backend is running: `curl http://localhost:8000/health` |
| CORS error | Check CORS_ORIGINS in backend/.env |

---

## Test Operator Role 👤

```bash
# Add operator user to DB
psql -U vending -d vending << EOF
INSERT INTO users (telegram_user_id, first_name, role, is_active)
VALUES (987654321, 'Test Operator', 'operator', true);
EOF
```

Then:
1. Login with operator's Telegram ID
2. Try to access /owner-report
3. Should see: **"Доступ запрещен"** ✅

---

## Production Deploy 🚀

```bash
# Update .env for production
TELEGRAM_BOT_TOKEN=<real token>
TELEGRAM_BOT_USERNAME=<real username>
SECRET_KEY=<generate new long secret>
DEBUG=False
CORS_ORIGINS=https://yourdomain.com
```

Then:
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## Documentation 📚

- **[TELEGRAM_SETUP.md](./TELEGRAM_SETUP.md)** - Full setup guide
- **[TELEGRAM_OAUTH_IMPLEMENTATION.md](./TELEGRAM_OAUTH_IMPLEMENTATION.md)** - Architecture & details
- **[API_REFERENCE.md](./API_REFERENCE.md)** - API endpoints

---

## Next Steps 📋

- [ ] Setup Telegram Bot
- [ ] Configure .env files
- [ ] Add users to database
- [ ] Test OAuth flow
- [ ] Test RBAC (owner vs operator)
- [ ] Deploy to production
- [ ] Monitor logs

---

**Done! Your Telegram OAuth is ready.** 🎉

Questions? Check [TELEGRAM_SETUP.md](./TELEGRAM_SETUP.md) or [DEBUG_GUIDE.md](./DEBUG_GUIDE.md)
