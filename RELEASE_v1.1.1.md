# Release v1.1.1 - MVP Polish

**Release Date:** 2025-01-XX
**Version:** v1.1.1
**Base:** v1.1.0 + STAGE 19 enhancements
**Status:** Ready for production deployment

---

## What's New in v1.1.1

### 🎯 Focus
Professional-grade MVP features: Filters, CSV export/import, sync management, deployment guardrails.

### ✨ Features Added

#### 1. Transaction Filtering & Export 📊
- **Advanced filters:** Date range, terminal ID, sum type (sales/returns/all)
- **CSV export:** Download filtered transactions as CSV
- **Smart pagination:** Page-based with total_pages calculation
- **Location:** InventoryPage.tsx

#### 2. Machine Matrix CSV Import 📥
- **Two-step import:** Dry-run preview → apply
- **Validation:** Type checking, range validation, error reporting
- **Bulk upsert:** Efficient ON CONFLICT handling
- **Location:** ButtonsPage.tsx

#### 3. Sync Runs History & Rerun 🔄
- **Date filtering:** Filter sync runs by date range
- **Rerun capability:** Re-execute previous syncs with same parameters
- **One-click rerun:** Popconfirm modal with original parameters
- **Location:** SettingsPage.tsx

#### 4. Deployment Guardrails 🛡️
- **API prefix check:** Prevents /api/v1/api/v1 duplicates
- **Pre-build hook:** Runs automatically during `npm run build`
- **Fail-fast:** Stops deployment if duplicates detected

---

## Technical Changes

### Backend Enhancements
- **GET /api/v1/transactions:** Page-based pagination, date_from/date_to, sum_type filter
- **GET /api/v1/transactions/export:** CSV streaming with proper headers
- **POST /api/v1/mapping/matrix/import:** Dry-run validation + apply import
- **GET /api/v1/sync/runs:** Date range filtering
- **POST /api/v1/sync/runs/{id}/rerun:** Re-execute previous sync

### Frontend Updates
- **InventoryPage.tsx:** DatePicker filters, sum_type select, CSV button
- **ButtonsPage.tsx:** CSV upload with dry-run modal and preview
- **SettingsPage.tsx:** Sync runs filter with rerun button
- **API clients:** Updated transactions.ts, mapping.ts, sync.ts

### Build System
- **scripts/check-api-prefix.js:** Guardrail enforcement
- **package.json:** `prebuild` hook integrated into build process

---

## Backward Compatibility

✅ **Fully backward compatible with v1.1.0**
- Old endpoints unchanged
- New features are additions only
- No breaking API changes
- No database migrations required

---

## Deployment Instructions

### 1. Build Backend
```bash
cd backend
docker build -t vending-admin:v1.1.1 .
```

### 2. Build Frontend
```bash
cd frontend
npm install
npm run build  # Runs guardrail check automatically
```

### 3. Push to Registry
```bash
docker push vending-admin:v1.1.1
```

### 4. Deploy
```bash
# Update docker-compose.prod.yml with new image tag
docker-compose -f docker-compose.prod.yml up -d
```

---

## Testing Checklist

- ✅ Transaction filters (date, terminal, sum_type)
- ✅ CSV export downloads correctly
- ✅ Mapping CSV dry-run preview
- ✅ Mapping CSV apply imports correctly
- ✅ Sync runs history with date filters
- ✅ Sync rerun executes with original parameters
- ✅ Build fails if API prefix duplicates detected
- ✅ RBAC enforcement (owner-only endpoints)
- ✅ JWT authentication required

---

## Known Limitations

1. CSV import limited to ~1000 rows per upload (memory constraint)
2. Sync rerun cannot modify original parameters
3. CSV export only includes transactions table columns
4. No scheduled sync (manual only)

---

## Performance Impact

- **Minimal:** New features are additions to existing functionality
- **CSV streaming:** Memory-efficient for large exports
- **Pagination:** Page-based reduces memory usage vs offset/limit
- **Database:** No schema changes, existing indices still valid

---

## Security Notes

- ✅ All owner-endpoints require JWT authentication
- ✅ Role-based access control enforced (owner role)
- ✅ CSV validation prevents malformed imports
- ✅ API prefix guardrail prevents endpoint misconfiguration
- ✅ No sensitive data in CSV headers

---

## Support & Documentation

- See [STAGE_19_COMPLETION.md](./STAGE_19_COMPLETION.md) for detailed implementation
- API reference: [API_REFERENCE.md](./API_REFERENCE.md)
- Setup guide: [QUICK_START.md](./QUICK_START.md)

---

## Version History

- **v1.1.1** (2025-01-XX) - MVP Polish (filters, export, import, guardrails)
- **v1.1.0** (2024-12-XX) - UI Unlock (real API endpoints)
- **v1.0.7** (2024-11-XX) - Initial release

---

## Contributors

- Feature implementation: Backend (Python), Frontend (TypeScript/React)
- Testing: Smoke tests on all endpoints
- Deployment: Docker build & push

---

**Status:** 🚀 Ready for production
**QA Sign-off:** ✅ Approved
**Deployment Date:** [Set by ops team]
