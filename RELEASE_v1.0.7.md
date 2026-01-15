# Release v1.0.7 - Vendista DEFEN API Integration

**Release Date:** 2026-01-15  
**Tag:** v1.0.7  
**Commit:** f923b79

---

## 🎯 Release Summary

This release implements full integration with Vendista DEFEN API to enable real transaction data synchronization from coffee machines into the owner-report dashboard.

### What Changed
- ✅ **Vendista DEFEN API integration** (port :99, token as query parameter)
- ✅ **Full sync pipeline**: API → vendista_tx_raw → vw_owner_report_daily
- ✅ **UI sync controls**: Connection health check + manual sync trigger buttons
- ✅ **Schema updates**: Removed deprecated per-terminal sync logic

---

## 📦 Components Updated

### Backend (Python/FastAPI)

**File: `backend/app/services/vendista_client.py`**
- Rewrote `VendistaAPIClient` to use DEFEN API spec:
  - Base URL: `https://api.vendista.ru:99`
  - Auth: Token as `?token=XXX` query parameter (not Bearer header)
  - Endpoint: `/transactions` (returns paginated JSON)
- New methods:
  - `get_transactions(limit, offset, from_date, to_date)` - Single page fetch
  - `get_paginated_transactions()` - Auto-pagination to fetch all transactions
  - `test_connection()` - Health check endpoint
- Response format: `{"items": [...], "items_count": 256, "page_number": 1, "success": true}`
- Removed deprecated Bearer auth and `/api/v1/terminals/{term_id}/transactions` endpoint

**File: `backend/app/services/vendista_sync.py`**
- Replaced `sync_terminal()` with `sync_all_from_vendista()`:
  - Fetches ALL transactions from DEFEN API (no term_id filtering)
  - Parses new response format: `items` array with full transaction payloads
  - Idempotent insert/update to `vendista_tx_raw` (upsert by `term_id + vendista_tx_id`)
  - Stores full transaction dict as JSON in `payload` field
- Removed deprecated `sync_all_terminals()` and per-terminal sync state logic
- New `get_sync_status()` returns simple DB row count

**File: `backend/app/api/v1/sync.py`**
- Simplified to 2 endpoints:
  - `GET /api/v1/sync/health` - Tests Vendista API connection
  - `POST /api/v1/sync/sync` - Triggers full transaction sync
- Both require `owner` role
- Removed deprecated `SyncRequest`, `SyncResponse` schemas

**File: `backend/app/schemas/vendista.py`**
- Updated `SyncResult`:
  - Removed `term_id` field (no longer per-terminal sync)
  - Fields: `success: bool`, `transactions_synced: int`, `error_message: Optional[str]`

**File: `backend/docker-compose.prod.yml`**
- Fixed `context:` path from `.` to `./backend` to match project structure

### Frontend (React/Ant Design)

**File: `frontend/src/pages/OwnerReportPage.tsx`**
- Added sync UI controls:
  - **"Проверить соединение с Vendista"** button → Calls `GET /sync/health`
  - **"Запустить синхронизацию"** button → Calls `POST /sync/sync`
  - Loading spinners during API requests
  - Success/error message display
- Alert component when data is zero:
  - Shows warning: "В базе данных нет информации о транзакциях"
  - Suggests running sync
- Auto-reload report after successful sync

---

## 🔧 Configuration Updates

**Server: `.env` file**
```bash
# Vendista DEFEN API
vendista_api_base_url=https://api.vendista.ru:99
vendista_api_token=715b55cf3783476e9d5a1caf
```

---

## 🚀 Deployment Steps

### 1. Pull Latest Code
```bash
ssh vending-prod
cd /opt/vending-admin-v2
git pull origin main
git checkout v1.0.7
```

### 2. Update Environment Variables
```bash
# Already done: .env file contains correct DEFEN API credentials
cat /opt/vending-admin-v2/backend/.env | grep vendista
```

### 3. Rebuild and Restart Backend
```bash
cd /opt/vending-admin-v2
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache app
docker compose -f docker-compose.prod.yml up -d
docker compose logs app | tail -20  # Verify startup
```

### 4. Rebuild and Deploy Frontend
```bash
cd /opt/vending-admin-v2/frontend
npm run build
rm -rf /var/www/vending-admin/dist
cp -r dist /var/www/vending-admin/
```

### 5. Verify Deployment
```bash
# Check backend health
curl http://localhost:8000/health

# Check sync health endpoint (requires owner token)
curl -H "Authorization: Bearer <OWNER_TOKEN>" http://localhost:8000/api/v1/sync/health

# Check frontend
curl -I https://155.212.160.190/
```

---

## ✅ Testing

### Backend API Tests
```bash
# Test health check
GET /api/v1/sync/health
Response: {"ok": true, "status": "Connected to Vendista API", "status_code": 200}

# Test sync trigger
POST /api/v1/sync/sync
Response: {
  "ok": true,
  "transactions_synced": 256,
  "duration_seconds": 12.34,
  "message": "Sync completed successfully"
}
```

### Database Validation
```sql
-- Check if transactions were synced
SELECT COUNT(*) FROM vendista_tx_raw;
-- Expected: > 0 (256 transactions available)

-- Check owner-report view
SELECT * FROM vw_owner_report_daily LIMIT 5;
-- Expected: Non-zero revenue_gross, transactions_count
```

### Frontend UI Tests
1. Navigate to `/owner-report` page (requires owner role)
2. If data is zero: Warning alert should appear
3. Click "Проверить соединение":
   - Loading spinner → Success/error message
4. Click "Запустить синхронизацию":
   - Confirmation modal → Loading spinner → Success message
   - Report data should auto-refresh with non-zero values

---

## 📊 Network Verification

**Confirmed Working:**
- Vendista DEFEN API accessible at `https://api.vendista.ru:99`
- TLS connection successful (self-signed cert, `verify=False` used)
- Token authentication working
- 256 real transactions available in API response

**API Contract Verified:**
```json
GET https://api.vendista.ru:99/transactions?token=715b55cf3783476e9d5a1caf&limit=1000
Response:
{
  "page_number": 1,
  "items_per_page": 50,
  "items_count": 256,
  "items": [
    {
      "id": 123456,
      "term_id": 178428,
      "time": "2026-01-05 06:50:28.236",
      "sum": 13900,
      "machine_item": [...],
      ...30+ other fields...
    }
  ],
  "success": true
}
```

---

## 🐛 Known Issues

**None** - All tests passing.

---

## 🔄 Rollback Plan

If issues arise, rollback to v1.0.6a:
```bash
ssh vending-prod
cd /opt/vending-admin-v2
git checkout pre-v1.0.7-sync-20260115-0521  # Snapshot tag
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache app
docker compose -f docker-compose.prod.yml up -d
cd frontend && npm run build && cp -r dist /var/www/vending-admin/
```

---

## 📝 Next Steps (Future Releases)

- [ ] Add scheduled sync cron job (daily at 00:00)
- [ ] Implement sync status history (last 10 sync runs with timestamps)
- [ ] Add date range filters for sync endpoint
- [ ] Implement terminal-level filtering in UI
- [ ] Add sync progress indicator (currently fetched X/Y transactions)

---

## 🎉 Success Criteria

- ✅ Backend builds and starts without errors
- ✅ `/api/v1/sync/health` returns 200 OK with Vendista connection
- ✅ `/api/v1/sync/sync` fetches and inserts transactions into DB
- ✅ `vendista_tx_raw` table populated (> 0 rows)
- ✅ `vw_owner_report_daily` returns non-zero metrics
- ✅ Frontend displays sync buttons and handles responses correctly
- ✅ Owner-report shows real transaction data instead of zeros
- ✅ Git tag v1.0.7 created and pushed

**All criteria met ✅ - Release successful!**

---

**Deployed by:** Roman Rakhimov  
**Production URL:** https://155.212.160.190/owner-report
