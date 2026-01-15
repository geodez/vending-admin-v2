╔════════════════════════════════════════════════════════════════════════════╗
║                   STAGE 19 — MVP POLISH IMPLEMENTATION PLAN                 ║
║              (Транзакции + Маппинг CSV + Sync Runs + Guardrails)           ║
╚════════════════════════════════════════════════════════════════════════════╝

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ OVERVIEW                                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Целевой результат: v1.1.1
- Backend: 4 новых endpoint контракта (transactions фильтры/экспорт, mapping import, sync)
- Frontend: 3 страницы с новыми фильтрами/кнопками (Inventory, Buttons, Settings)
- Guardrails: npm build блокирует /api/v1/api/v1
- Release: RELEASE_v1.1.1.md + tag v1.1.1

Без редизайна, без смены меню, только "начинка" и MVP-функции.

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 1: BACKEND IMPLEMENTATION                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

TASK 19.1.1 — GET /api/v1/transactions КОНТРАКТ
──────────────────────────────────────────────

Файл: backend/app/api/v1/transactions.py (ОБНОВИТЬ)

Текущий контракт:
  - skip, limit (offset-based)
  
Новый контракт (page-based):
  GET /api/v1/transactions
    Параметры:
      date_from?: str (YYYY-MM-DD)
      date_to?: str (YYYY-MM-DD)
      term_id?: int
      sum_type?: enum[all, positive, non_positive] = "positive"
      page?: int = 1 (>=1)
      page_size?: int = 50 (1..200)
      order_desc?: bool = true
    
    Returns:
      {
        "items": [
          {
            "id": int,
            "tx_time": datetime,
            "term_id": int,
            "vendista_tx_id": str,
            "sum_rub": float,
            "sum_kopecks": int,
            "machine_item_id": int | null,
            "terminal_comment": str | null,
            "status": str | null,
            "raw_payload": dict (original JSON)
          },
          ...
        ],
        "page": int,
        "page_size": int,
        "total": int,
        "total_pages": int
      }

Logic:
  - sum_type="positive" => WHERE (payload->>'sum')::float > 0
  - sum_type="non_positive" => WHERE (payload->>'sum')::float <= 0
  - sum_type="all" => no sum filter
  - date filter на vendista_tx_raw.tx_time
  - term_id filter на payload->>'term_id'
  - ORDER BY tx_time DESC by default
  - RBAC: owner-only

TASK 19.1.2 — GET /api/v1/transactions/export CSV
──────────────────────────────────────────────────

Файл: backend/app/api/v1/transactions.py (НОВЫЙ ENDPOINT)

GET /api/v1/transactions/export
  Параметры: те же, что и в GET /transactions
  
  Returns:
    Content-Type: text/csv
    Content-Disposition: attachment; filename="transactions_YYYYMMDD_YYYYMMDD.csv"
    
    CSV содержит заголовок:
      tx_time,term_id,vendista_tx_id,sum_rub,sum_kopecks,machine_item_id,terminal_comment,status
    
    И строки для каждого item (тот же фильтр, что и /transactions)
    
Logic:
  - Использовать io.StringIO() + csv.DictWriter
  - Логировать: export с параметрами и количество строк
  - RBAC: owner-only

TASK 19.2.1 — POST /api/v1/mapping/matrix/import DRY-RUN
────────────────────────────────────────────────────────

Файл: backend/app/api/v1/mapping.py (НОВЫЙ ENDPOINT)

POST /api/v1/mapping/matrix/import?dry_run=true
  Принимает: multipart/form-data { file: csv }
  
  CSV формат (без заголовка или с заголовком):
    term_id,machine_item_id,drink_id,location_id
    178428,1,5,1
    ...
  
  Returns (при dry_run=true):
    {
      "dry_run": true,
      "total_rows": int,
      "valid_rows": int,
      "invalid_rows": int,
      "to_insert": int (rows that будут inserted),
      "to_update": int (rows that будут updated),
      "unchanged": int (rows что не изменятся),
      "errors": [
        {
          "row": 12,
          "code": "INVALID_DRINK_ID" | "MISSING_TERM_ID" | "MISSING_MACHINE_ITEM_ID" | "INVALID_LOCATION_ID",
          "message": str,
          "raw": {term_id: ..., machine_item_id: ...}
        },
        ...
      ],
      "preview": [
        {
          "row": 1,
          "term_id": 178428,
          "machine_item_id": 1,
          "drink_id": 5,
          "location_id": 1,
          "action": "insert" | "update" | "noop",
          "before": {...} | null,
          "after": {...}
        },
        ...
      ]
    }

Validation:
  - term_id: обязателен, int
  - machine_item_id: обязателен, int
  - drink_id: обязателен, int, должен существовать в таблице drinks
  - location_id: если не задан, попытаться инфер из term_id (если есть mapping),
                 иначе ошибка

Action determination:
  - SELECT * FROM machine_matrix WHERE term_id=X AND machine_item_id=Y
  - если не найдено => action="insert"
  - если найдено и значения отличаются => action="update"
  - если найдено и значения совпадают => action="noop"

RBAC: owner-only
LOGGING: dry-run параметры и результаты

TASK 19.2.2 — POST /api/v1/mapping/matrix/import APPLY
────────────────────────────────────────────────────────

Файл: backend/app/api/v1/mapping.py (ОБНОВИТЬ)

POST /api/v1/mapping/matrix/import?dry_run=false
  (Параметры и CSV формат как в Task 19.2.1)
  
  Returns (при dry_run=false):
    {
      "dry_run": false,
      "applied": true,
      "total_rows": int,
      "inserted": int,
      "updated": int,
      "unchanged": int,
      "errors": [... same as dry_run],
      "applied_count": int (inserted + updated)
    }

Logic:
  - Для каждой валидной строки: INSERT ... ON CONFLICT (term_id, machine_item_id)
    DO UPDATE SET drink_id = ..., location_id = ...
  - Для невалидных строк: собрать в errors[]
  - Если есть ошибки AND есть валидные строки: все равно применить валидные
  - После успешного import: в логи (количество измененных)
  - RBAC: owner-only

TASK 19.3.1 — GET /api/v1/sync/runs ФИЛЬТР
─────────────────────────────────────────────

Файл: backend/app/api/v1/sync.py (ОБНОВИТЬ)

GET /api/v1/sync/runs
  Параметры:
    date_from?: str (YYYY-MM-DD)
    date_to?: str (YYYY-MM-DD)
    limit?: int = 50 (1..200)
    offset?: int = 0
  
  Returns:
    {
      "items": [
        {
          "id": int,
          "started_at": datetime,
          "completed_at": datetime | null,
          "period_start": date | null,
          "period_end": date | null,
          "fetched": int | null,
          "inserted": int | null,
          "skipped_duplicates": int | null,
          "ok": bool | null,
          "message": str | null,
          "duration_seconds": float (calculated: completed_at - started_at)
        },
        ...
      ],
      "total": int,
      "limit": int,
      "offset": int
    }

Logic:
  - date_from/date_to фильтр на started_at
  - ORDER BY started_at DESC
  - RBAC: owner-only (или public для health check?)

TASK 19.3.2 — POST /api/v1/sync/sync ГАРАНТИРОВАННАЯ ЗАПИСЬ
────────────────────────────────────────────────────────────

Файл: backend/app/api/v1/sync.py (ОБНОВИТЬ)

Текущий endpoint: POST /api/v1/sync/sync
Параметры: period_start, period_end

Изменение:
  1) ДО fetch: создать sync_runs row
     INSERT INTO sync_runs (started_at, period_start, period_end, ok)
     VALUES (NOW(), period_start, period_end, NULL)
     RETURNING id
     
  2) После успешного fetch/insert:
     UPDATE sync_runs SET
       completed_at = NOW(),
       fetched = count_from_api,
       inserted = count_inserted,
       skipped_duplicates = count_skipped,
       expected_total = count_expected,
       pages_fetched = pages,
       items_per_page = items_per_page,
       last_page = last_page_num,
       ok = true,
       message = 'OK'
     WHERE id = run_id
     
  3) В случае exception:
     UPDATE sync_runs SET
       completed_at = NOW(),
       ok = false,
       message = str(exception)
     WHERE id = run_id
     ROLLBACK (или автоматический, в зависимости от типа ошибки)

Returns: {status, message, counters...} как было

RBAC: owner-only

TASK 19.3.3 — POST /api/v1/sync/runs/{id}/rerun
────────────────────────────────────────────────

Файл: backend/app/api/v1/sync.py (НОВЫЙ ENDPOINT)

POST /api/v1/sync/runs/{id}/rerun

Logic:
  1) SELECT period_start, period_end FROM sync_runs WHERE id = {id}
  2) Вызвать sync как в POST /sync/sync с этими параметрами
  3) Возвращает новый run (с новым id)

Returns:
  {
    "status": "ok" | "error",
    "new_run_id": int,
    "message": str
  }

RBAC: owner-only

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 2: FRONTEND IMPLEMENTATION                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

TASK 19.1.3 — InventoryPage.tsx ФИЛЬТРЫ
──────────────────────────────────────

Файл: frontend/src/pages/InventoryPage.tsx (ОБНОВИТЬ)

Добавить фильтры в существующей layout:
  
  Сверху таблицы добавить row с элементами управления:
  
  [DatePicker DateFrom] [DatePicker DateTo]
  [Select Терминал] [Radio/Toggle: Продажи|Возвраты|Все]
  [Button Применить Фильтр] [Button Экспорт CSV]

State:
  const [filters, setFilters] = useState({
    dateFrom: null,
    dateTo: null,
    termId: null,
    sumType: 'positive', // 'all' | 'positive' | 'non_positive'
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

API Call:
  useEffect(() => {
    transactionsApi.getTransactions({
      date_from: filters.dateFrom,
      date_to: filters.dateTo,
      term_id: filters.termId,
      sum_type: filters.sumType,
      page: page,
      page_size: pageSize,
    })
    .then(data => {
      setTransactions(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    })
  }, [filters, page, pageSize])

Table:
  - Добавить колону "Тип" с бейджем для sum <= 0 (badge: "ВОЗВРАТ")
  - Сумма по умолчанию в рублях (не копейки)
  - Пагинация: показывать page/total_pages и кнопки prev/next

CSV Button:
  onClick={() => {
    transactionsApi.exportTransactions(filters)
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transactions_${dateFrom}_${dateTo}.csv`;
        a.click();
      })
  }}

TASK 19.2.3 — ButtonsPage.tsx CSV IMPORT UI
───────────────────────────────────────────

Файл: frontend/src/pages/ButtonsPage.tsx (ОБНОВИТЬ)

Добавить upload + dry-run modal (без изменения существующей таблицы):

Сверху таблицы:
  [FileInput type="file" accept=".csv"] [Button Проверить]

При click "Проверить":
  1) mappingApi.importMatrixDryRun(file)
  2) Открыть модал с результатами:
     - summary: total_rows, valid_rows, invalid_rows, to_insert/update/unchanged
     - errors таблица (если есть)
     - preview таблица (что изменится)
  3) Если нет errors: [Button Применить]
  4) При click "Применить":
     mappingApi.importMatrixApply(file)
     закрыть модал, рефреш таблицы

State:
  const [uploadFile, setUploadFile] = useState(null);
  const [dryRunResult, setDryRunResult] = useState(null);
  const [showDryRunModal, setShowDryRunModal] = useState(false);

TASK 19.3.4 — SettingsPage.tsx SYNC RUNS UI
────────────────────────────────────────────

Файл: frontend/src/pages/SettingsPage.tsx (ОБНОВИТЬ)

Обновить существующую таблицу sync runs:

Добавить фильтры сверху:
  [DatePicker DateFrom] [DatePicker DateTo] [Button Применить]

Таблица columns:
  started_at, period (period_start..period_end), duration, fetched, inserted, skipped, ok (status)
  + колона Action с [Button Повторить]

При click "Повторить":
  1) ConfirmModal("Повторить синхронизацию за период XX..YY?")
  2) syncApi.rerumSyncRun(runId)
  3) Рефреш таблицы

State:
  const [filters, setFilters] = useState({
    dateFrom: null,
    dateTo: null,
  });

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 3: GUARDRAILS & BUILD                                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

TASK 19.4.1 — npm run check:api-prefix ENFORCEMENT
──────────────────────────────────────────────────

Файл: frontend/package.json (ОБНОВИТЬ)

Проверить наличие скрипта check:api-prefix:
  "check:api-prefix": "grep -r '/api/v1/' src --include='*.ts' --include='*.tsx' | grep -v 'baseURL' | grep -v '//' | ...",
  
  или создать скрипт scripts/check-api-prefix.js

Добавить prebuild:
  "prebuild": "npm run check:api-prefix",
  "build": "vite build"

Скрипт должен:
  - Найти все файлы .ts/.tsx в src/
  - Искать строки типа "/api/v1/" (но не в комментариях)
  - Исключить baseURL и комментарии
  - Если найдёт дублирующиеся вызовы типа:
    apiClient.get("/api/v1/...") или
    `${baseURL}/api/v1/api/v1/...`
  - Выйти с ошибкой 1

TASK 19.4.2 — BUILD BLOCK ON GUARD FAILURE
──────────────────────────────────────────

Файл: frontend/package.json (ВЫШЕ) + frontend/scripts/check-api-prefix.js (СОЗДАТЬ)

При npm run build:
  1) Сначала выполнится prebuild (check:api-prefix)
  2) Если check найдёт нарушения => exit 1 => build fails
  3) Вывести в консоль: "❌ API prefix guard failed: /api/v1/api/v1 detected!"

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PHASE 4: ACCEPTANCE & RELEASE                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

ACCEPTANCE TESTS (CURL)
──────────────────────

OWNER_JWT="<generated in server>"

1) TRANSACTIONS FILTERS
   curl -sS -H "Authorization: Bearer $OWNER_JWT" \
     'http://127.0.0.1:8000/api/v1/transactions/?date_from=2026-01-01&date_to=2026-01-15&sum_type=positive&page=1&page_size=50' \
     | jq '.total, .items | length'
   
   Expected: total=348, items.length=50

2) TRANSACTIONS NON-POSITIVE
   curl -sS -H "Authorization: Bearer $OWNER_JWT" \
     'http://127.0.0.1:8000/api/v1/transactions/?date_from=2026-01-01&date_to=2026-01-15&sum_type=non_positive&page=1&page_size=50' \
     | jq '.total'
   
   Expected: total=7

3) CSV EXPORT
   curl -sS -H "Authorization: Bearer $OWNER_JWT" \
     -o /tmp/tx.csv \
     'http://127.0.0.1:8000/api/v1/transactions/export?date_from=2026-01-01&date_to=2026-01-15&sum_type=positive'
   wc -l /tmp/tx.csv
   
   Expected: 348 rows + 1 header = 349 lines

4) MAPPING DRY-RUN
   curl -sS -F "file=@test.csv" -H "Authorization: Bearer $OWNER_JWT" \
     'http://127.0.0.1:8000/api/v1/mapping/matrix/import?dry_run=true' \
     | jq '.errors, .preview | length'
   
   Expected: errors=0, preview has rows

5) MAPPING APPLY
   curl -sS -F "file=@test.csv" -H "Authorization: Bearer $OWNER_JWT" \
     'http://127.0.0.1:8000/api/v1/mapping/matrix/import?dry_run=false' \
     | jq '.applied, .applied_count'
   
   Expected: applied=true, applied_count>0

6) SYNC RUNS FILTER
   curl -sS -H "Authorization: Bearer $OWNER_JWT" \
     'http://127.0.0.1:8000/api/v1/sync/runs?date_from=2026-01-01&date_to=2026-01-15&limit=20' \
     | jq '.items | length, .[0].duration_seconds'
   
   Expected: items with duration_seconds calculated

7) SYNC RERUN
   RUN_ID=<last run id from sync/runs>
   curl -sS -X POST -H "Authorization: Bearer $OWNER_JWT" \
     'http://127.0.0.1:8000/api/v1/sync/runs/$RUN_ID/rerun' \
     | jq '.new_run_id, .status'
   
   Expected: new_run_id > RUN_ID, status=ok

8) GUARD CHECK
   npm run check:api-prefix
   
   Expected: exit 0, no /api/v1/api/v1 found

RELEASE (COMMITS & TAG)
──────────────────────

git add backend/app/api/v1/transactions.py
git commit -m "feat(transactions): filters + pagination contract + csv export"

git add backend/app/api/v1/mapping.py
git commit -m "feat(mapping): csv import dry-run + apply with validation"

git add backend/app/api/v1/sync.py
git commit -m "feat(sync): runs filter + rerun + guaranteed history recording"

git add frontend/src/pages/InventoryPage.tsx \
         frontend/src/pages/ButtonsPage.tsx \
         frontend/src/pages/SettingsPage.tsx \
         frontend/package.json \
         frontend/scripts/check-api-prefix.js
git commit -m "feat(frontend): transactions filters + mapping csv ui + sync runs ui + guard enforcement"

git add RELEASE_v1.1.1.md
git commit -m "docs: RELEASE_v1.1.1.md - mvp polish (filters, csv, dry-run, rerun)"

git tag -a v1.1.1 -m "Release v1.1.1: MVP polish - transactions filters, mapping csv import, sync rerun"
git push origin main v1.1.1

DEPLOY
──────

Server:
  cd /opt/vending-admin-v2/backend
  docker compose -f docker-compose.prod.yml up -d --build app
  
Frontend:
  cd /opt/vending-admin-v2/frontend
  npm ci && npm run build
  cp -r dist/* /var/www/vending-admin/
  systemctl reload nginx

Final checks:
  curl -I https://roman.razdobreev.fvds.ru/ (200 OK)
  DevTools: нет /api/v1/api/v1 запросов

╔════════════════════════════════════════════════════════════════════════════╗
║             TIMELINE & DEPENDENCIES                                        ║
╚════════════════════════════════════════════════════════════════════════════╝

Фаза 1 (Backend):   Tasks 19.1.1 → 19.3.3  (параллель возможна)
Фаза 2 (Frontend):  Tasks 19.1.3, 19.2.3, 19.3.4  (зависит от Фазы 1)
Фаза 3 (Guards):    Tasks 19.4.1, 19.4.2  (независима)
Фаза 4 (Acceptance): все Acceptance тесты
Release:            commits + tag v1.1.1 + deploy

Примерный размер работ:
  - Backend:  ~500 строк кода (3 файла, 5 endpoint'ов)
  - Frontend: ~300 строк кода (3 файла, фильтры + UI)
  - Guardrails: ~100 строк (скрипт + config)
  - Итого: ~900 строк код + doc

Готов к STAGE 19.1 реализации? Начнём с Backend.
