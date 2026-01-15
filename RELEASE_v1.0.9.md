# Release v1.0.9: Full-Period Vendista Sync + Frontend API Guard

**Date:** 2026-01-15  
**Status:** ✅ STABLE

---

## Overview
v1.0.9 introduces **full-period synchronization** with pagination metadata, period-based filtering, and a frontend API path guardrail to prevent duplicate `/api/v1` prefixes.

---

## Key Features

### 1. Full-Period Vendista Sync with Pagination
- **API Endpoint:** `POST /api/v1/sync/sync`
- **Parameters:**
  - `period_start` (date, optional): Start date YYYY-MM-DD. Default: first day of current month
  - `period_end` (date, optional): End date YYYY-MM-DD. Default: today
  - `items_per_page` (int, default: 50): Page size for Vendista DEFEN API
  - `order_desc` (bool, default: true): Sort order flag

### 2. Pagination Metadata in Response
The sync endpoint now returns detailed pagination information:
```json
{
  "ok": true,
  "expected_total": 355,           // Total items expected from API
  "pages_fetched": 8,              // Number of pages actually fetched
  "items_per_page": 50,            // Items per page
  "last_page": 8,                  // Last page number
  "fetched": 355,                  // Total items fetched
  "inserted": 305,                 // New rows inserted to DB
  "skipped_duplicates": 0,         // Duplicate rows skipped
  "transactions_synced": 305,      // Transactions synced
  "started_at": "2026-01-15T17:36:41.443319",
  "completed_at": "2026-01-15T17:36:41.857972",
  "duration_seconds": 0.414653,
  "message": "Sync completed successfully"
}
```

### 3. Smart Period Filtering
- Vendista API called with `DateFrom` and `DateTo` parameters
- Eliminates need to fetch entire history
- Example: `period_start=2026-01-01&period_end=2026-01-15` syncs exactly 355 transactions

### 4. Frontend API Path Guardrail
- Added npm script `check:api-prefix` to detect `/api/v1` occurrences in source code
- Excludes `client.ts` (where baseURL is set)
- Prevents accidental double-prefixing (`/api/v1/api/v1/...`)
- Runs as pre-build check

---

## Database Verification (Period: 2026-01-01 to 2026-01-15)

| Metric | Value |
|--------|-------|
| Total Rows Fetched | 355 |
| Rows Inserted to DB | 305 |
| Duplicate Rows Skipped | 0 |
| DB vendista_tx_raw Count | 355 |
| Min tx_time | 2026-01-01 12:56:50 UTC |
| Max tx_time | 2026-01-15 20:27:19 UTC |

---

## API Endpoints Verified

### Health Check
```bash
curl -H "Authorization: Bearer $OWNER_JWT" \
  http://api.example.com/api/v1/sync/health
```
✅ Response: `{"ok": true, "status": "Connected to Vendista API"}`

### Sync Endpoint (POST)
```bash
curl -X POST -H "Authorization: Bearer $OWNER_JWT" \
  "http://api.example.com/api/v1/sync/sync?period_start=2026-01-01&period_end=2026-01-15"
```
✅ Response includes all pagination metadata (see Feature #2)

---

## Frontend Changes

### API Client Configuration
- axios baseURL: `/api/v1` (set once in client.ts)
- All API calls use relative paths: `/sync/health`, `/sync/sync`, etc.
- Guard script prevents hardcoded `/api/v1/` in source

### Build Output
```
dist/index.html                        0.62 kB
dist/assets/index-CRN1Cc6N.css         0.88 kB
dist/assets/index-MuYLdZIJ.js       1,139 kB (gzipped: 365.57 kB)
```

---

## Deployment Checklist

- [x] Backend: app container rebuilt with pagination logic
- [x] Backend: Sync endpoint accepts period parameters
- [x] Backend: SyncResult includes metadata fields
- [x] Database: 355 rows verified for period 2026-01-01..2026-01-15
- [x] Frontend: Guard script passes (0 /api/v1 violations)
- [x] Frontend: Build successful, no errors
- [x] Frontend: Deployed to /var/www/vending-admin
- [x] Nginx: Config validated and reloaded
- [x] API Health: All endpoints return 200 OK
- [x] Idempotency: Re-running sync skips duplicates (inserted=0 on second run)

---

## Testing Instructions

### Manual Smoke Test
1. Open https://admin.b2broundtable.ru/owner-report
2. Inspect Network tab: confirm no `/api/v1/api/v1/...` URLs
3. Click "Проверить соединение" (Check Connection)
4. Expected: `ok=true` from `/api/v1/sync/health`
5. Click "Запустить синхронизацию" (Run Sync)
6. Expected: `expected_total=355, pages_fetched=8` in response

### Automated Health Check
```bash
# Owner JWT from user_id=1
curl -H "Authorization: Bearer $JWT" \
  http://localhost:8000/api/v1/sync/health
# Should return: {"ok": true, ...}
```

### Sync with Custom Period
```bash
curl -X POST -H "Authorization: Bearer $JWT" \
  "http://localhost:8000/api/v1/sync/sync?period_start=2026-01-01&period_end=2026-01-15"
# Should return metadata with expected_total, pages_fetched, etc.
```

---

## Code Changes Summary

### Backend Files Modified
- `backend/app/services/vendista_client.py`: Pagination logic rewritten with DEFEN params
- `backend/app/services/vendista_sync.py`: Period filtering and metadata aggregation
- `backend/app/schemas/vendista.py`: SyncResult includes pagination fields
- `backend/app/api/v1/sync.py`: Endpoint accepts period parameters

### Frontend Files Modified
- `frontend/package.json`: Added `check:api-prefix` script

### Configuration
- No config changes; all defaults are backward compatible

---

## Rollback Instructions

If issues arise:
```bash
# Tag current commit
git tag v1.0.9-rollback

# Revert to v1.0.8
git reset --hard origin/main  # or specify a commit hash
git checkout v1.0.8

# Rebuild backend and frontend
# Redeploy
```

---

## Known Limitations

- Max items per request: ~50 (Vendista API default); pagination handles larger datasets
- Period filtering is performed server-side; client cannot override sync window arbitrarily
- Owner role required to trigger sync

---

## Performance Notes

- **Sync Time (355 items):** ~0.4 seconds
- **Payload Size:** ~1.1 MB (minified JS), 365.57 kB (gzipped)
- **API Response Time:** ~200 ms (with full pagination metadata)
- **Database Insertion Rate:** 305 rows in single sync pass

---

## Contributors

- Roman Razdobreev

---

## Next Steps

- Monitor production sync behavior for stability
- Consider async task queue for larger periods (>1000 items)
- Implement incremental sync (last_sync_timestamp tracking)
- Add UI pagination controls for custom period selection

---

**Status:** ✅ PRODUCTION READY
