# API Reference

> **Важно:** Этот документ является справочником на основе **старого проекта** [geodez/vending](https://github.com/geodez/vending).  
> Используется для понимания структуры данных Vendista API и бизнес-логики.

---

## 📡 Vendista API (внешний источник данных)

### Base URL
```
https://api.vendista.ru
```

### Аутентификация
```http
Authorization: Bearer {VENDISTA_API_TOKEN}
```

### Endpoints

#### 1. Получение транзакций терминала

```http
GET /api/v1/terminals/{term_id}/transactions
```

**Query Parameters:**
- `from` — начало периода (ISO 8601 datetime)
- `to` — конец периода (ISO 8601 datetime)
- `limit` — количество транзакций (default: 100, max: 1000)

**Response:**
```json
{
  "transactions": [
    {
      "id": 123456789,
      "terminal_id": 145912,
      "timestamp": "2026-01-11T10:30:45Z",
      "machine_item_id": 1,
      "product_name": "Капучино 0.2л",
      "price": 100.00,
      "status": "success",
      "payload": {
        "Terminal Comment": "Островского Терм#1",
        "MachineItemId": 1,
        "fact_sum": 100.00,
        "price": 100.00
      }
    }
  ]
}
```

**Важные поля:**
- `machine_item_id` — ID кнопки на терминале (используется для привязки к рецептам)
- `Terminal Comment` — человеко-понятное имя терминала
- `fact_sum` — фактически полученная сумма
- `price` — цена продукта по прайсу

---

## 🗄️ База данных (PostgreSQL)

### Основные таблицы

#### `vendista_terminals`
Терминалы из Vendista API.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | ID терминала (PK) |
| title | TEXT | Название терминала |
| comment | TEXT | Комментарий (человеко-понятное имя) |
| is_active | BOOLEAN | Активен ли терминал |
| created_at | TIMESTAMPTZ | Дата создания |
| updated_at | TIMESTAMPTZ | Дата обновления |

---

#### `vendista_tx_raw`
Сырые транзакции из Vendista API.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | ID записи (PK, autoincrement) |
| term_id | BIGINT | ID терминала (FK) |
| vendista_tx_id | BIGINT | ID транзакции в Vendista |
| tx_time | TIMESTAMPTZ | Время транзакции |
| payload | JSONB | Полный JSON payload |
| inserted_at | TIMESTAMPTZ | Время вставки в БД |

**UNIQUE:** `(term_id, vendista_tx_id)`

**Пример payload:**
```json
{
  "Terminal Comment": "Островского Терм#1",
  "MachineItemId": 1,
  "fact_sum": 100.00,
  "price": 100.00,
  "product_name": "Капучино 0.2л"
}
```

---

#### `locations`
Локации (места установки терминалов).

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | INTEGER | ID локации (PK) |
| name | TEXT | Название локации (уникальное) |

**Пример:**
```sql
INSERT INTO locations (id, name) VALUES (1, 'Островского');
```

---

#### `products`
Продукты (напитки) из Vendista.

| Колонка | Тип | Описание |
|---------|-----|----------|
| product_external_id | INTEGER | ID продукта (PK) |
| name | TEXT | Название продукта |
| sale_price_rub | NUMERIC | Цена продажи (₽) |
| enabled | BOOLEAN | Активен ли продукт |
| visible | BOOLEAN | Видим ли продукт |
| meta | JSONB | Дополнительные данные |

---

#### `ingredients`
Ингредиенты для рецептов.

| Колонка | Тип | Описание |
|---------|-----|----------|
| ingredient_code | TEXT | Код ингредиента (PK) |
| ingredient_group | TEXT | Группа ингредиента (nullable) |
| brand_name | TEXT | Название бренда (nullable) |
| unit | TEXT | Единица измерения (г, мл, шт) |
| cost_per_unit_rub | NUMERIC | Цена за единицу (₽) |
| default_load_qty | NUMERIC | Количество по умолчанию при загрузке |
| alert_threshold | NUMERIC | Порог алерта (минимальный остаток) |
| display_name_ru | TEXT | Название на русском |
| unit_ru | TEXT | Единица измерения на русском |
| sort_order | INTEGER | Порядок сортировки |
| expense_kind | TEXT | Тип расхода: 'stock_tracked' или 'not_tracked' |
| is_stock_tracked | BOOLEAN | Участвует ли в остатках (deprecated, использовать expense_kind) |
| meta | JSONB | Дополнительные данные |

**Типы расхода:**
- `stock_tracked` — постоянный ингредиент (участвует в остатках и себестоимости)
- `not_tracked` — переменный ингредиент (только справочно)

**Пример:**
```sql
INSERT INTO ingredients (ingredient_code, unit, cost_per_unit_rub, expense_kind, display_name_ru, unit_ru)
VALUES ('COFFEE_BEANS', 'g', 1.90, 'stock_tracked', 'Кофе зерно', 'г');
```

---

#### `drinks`
Глобальный справочник напитков (рецептов).

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL | ID напитка (PK) |
| name | TEXT | Название напитка (уникальное) |
| is_active | BOOLEAN | Активен ли напиток |
| created_at | TIMESTAMPTZ | Дата создания |

**Пример:**
```sql
INSERT INTO drinks (name) VALUES ('Капучино');
```

---

#### `drink_items`
Состав рецепта (ингредиенты в напитке).

| Колонка | Тип | Описание |
|---------|-----|----------|
| drink_id | INTEGER | ID напитка (PK, FK) |
| ingredient_code | TEXT | Код ингредиента (PK, FK) |
| qty_per_unit | NUMERIC | Количество на 1 порцию |
| unit | TEXT | Единица измерения |

**PRIMARY KEY:** `(drink_id, ingredient_code)`

**Пример:**
```sql
-- Капучино: 18г кофе + 120мл молока
INSERT INTO drink_items (drink_id, ingredient_code, qty_per_unit, unit)
VALUES
  (1, 'COFFEE_BEANS', 18, 'g'),
  (1, 'MILK', 120, 'ml');
```

---

#### `location_drink_map`
Привязка напитков к кнопкам терминалов по локациям.

| Колонка | Тип | Описание |
|---------|-----|----------|
| location_id | INTEGER | ID локации (FK) |
| machine_item_id | TEXT | ID кнопки терминала |
| product_external_id | INTEGER | ID продукта (FK) |
| drink_id | INTEGER | ID напитка (FK, nullable) |
| is_active | BOOLEAN | Активна ли привязка |

**UNIQUE:** `(location_id, machine_item_id, product_external_id)`

**Пример:**
```sql
-- Привязка кнопки 1 к рецепту "Капучино" в локации "Островского"
INSERT INTO location_drink_map (location_id, machine_item_id, product_external_id, drink_id)
VALUES (1, '1', 101, 1);
```

---

#### `machine_matrix`
Маппинг кнопок терминала к продуктам и локациям.

| Колонка | Тип | Описание |
|---------|-----|----------|
| vendista_term_id | BIGINT | ID терминала (PK, FK) |
| machine_item_id | INTEGER | ID кнопки терминала (PK) |
| product_external_id | INTEGER | ID продукта (FK) |
| location_id | INTEGER | ID локации (FK, nullable) |
| comment | TEXT | Комментарий |

**PRIMARY KEY:** `(vendista_term_id, machine_item_id)`

**Пример:**
```sql
-- Терминал 145912, кнопка 1 -> продукт 101, локация 1
INSERT INTO machine_matrix (vendista_term_id, machine_item_id, product_external_id, location_id)
VALUES (145912, 1, 101, 1);
```

---

#### `ingredient_loads`
Загрузки ингредиентов на склад.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | BIGINT | ID загрузки (PK, autoincrement) |
| ts | TIMESTAMPTZ | Время загрузки |
| location_id | INTEGER | ID локации (FK) |
| ingredient_code | TEXT | Код ингредиента (FK) |
| qty_loaded | NUMERIC | Количество загружено |
| comment | TEXT | Комментарий (nullable) |

**Пример:**
```sql
-- Загрузка 10 кг кофе в локацию "Островского"
INSERT INTO ingredient_loads (ts, location_id, ingredient_code, qty_loaded, comment)
VALUES ('2026-01-11 10:00:00+03', 1, 'COFFEE_BEANS', 10000, 'Закупка недели');
```

---

#### `variable_expenses`
Переменные расходы.

| Колонка | Тип | Описание |
|---------|-----|----------|
| id | SERIAL | ID расхода (PK) |
| expense_date | DATE | Дата расхода |
| location_id | INTEGER | ID локации (FK) |
| category | TEXT | Категория расхода |
| amount_rub | NUMERIC | Сумма (₽) |
| comment | TEXT | Комментарий (nullable) |
| created_at | TIMESTAMPTZ | Дата создания записи |
| created_by | TEXT | Кто создал (username) |

**Категории (примеры):**
- `Аренда`
- `Транспорт`
- `Обслуживание`
- `Салфетки/стаканы`
- `Прочее`

**Пример:**
```sql
INSERT INTO variable_expenses (expense_date, location_id, category, amount_rub, comment, created_by)
VALUES ('2026-01-10', 1, 'Аренда', 15000, 'Месячная аренда', 'ivan_ivanov');
```

---

## 📊 Views (Представления)

### `vw_tx_cogs`
Транзакции с расчетом COGS и валовой прибыли.

**Логика:**
```sql
SELECT
  t.term_id,
  t.tx_time,
  t.machine_item_id,
  t.product_external_id,
  t.product_name,
  t.fact_sum AS revenue_rub,
  SUM(di.qty_per_unit * i.cost_per_unit_rub) AS cogs_rub,
  (t.fact_sum - SUM(di.qty_per_unit * i.cost_per_unit_rub)) AS gross_profit_rub
FROM vendista_tx_raw t
LEFT JOIN machine_matrix mm ON mm.vendista_term_id = t.term_id
  AND mm.machine_item_id = t.machine_item_id
LEFT JOIN location_drink_map ldm ON ldm.location_id = mm.location_id
  AND ldm.product_external_id = mm.product_external_id
LEFT JOIN drink_items di ON di.drink_id = ldm.drink_id
LEFT JOIN ingredients i ON i.ingredient_code = di.ingredient_code
  AND i.expense_kind = 'stock_tracked'  -- только постоянные ингредиенты
GROUP BY t.id;
```

**Поля:**
| Колонка | Описание |
|---------|----------|
| term_id | ID терминала |
| tx_time | Время транзакции |
| machine_item_id | ID кнопки |
| product_name | Название продукта |
| revenue_rub | Выручка (₽) |
| cogs_rub | Себестоимость (₽) |
| gross_profit_rub | Валовая прибыль (₽) |

---

### `vw_kpi_daily`
Ежедневные KPI по терминалам и локациям.

**Поля:**
| Колонка | Описание |
|---------|----------|
| day | День (DATE) |
| term_id | ID терминала |
| location_id | ID локации |
| tx_count | Количество транзакций |
| revenue_rub | Выручка (₽) |
| cogs_rub | Себестоимость (₽) |
| gross_profit_rub | Валовая прибыль (₽) |
| gross_margin_pct | Валовая маржа (%) |
| avg_check_rub | Средний чек (₽) |

**Логика:**
```sql
SELECT
  DATE(tx_time) AS day,
  term_id,
  location_id,
  COUNT(*) AS tx_count,
  SUM(revenue_rub) AS revenue_rub,
  SUM(cogs_rub) AS cogs_rub,
  SUM(gross_profit_rub) AS gross_profit_rub,
  (SUM(gross_profit_rub) / NULLIF(SUM(revenue_rub), 0) * 100) AS gross_margin_pct,
  (SUM(revenue_rub) / COUNT(*)) AS avg_check_rub
FROM vw_tx_cogs
GROUP BY day, term_id, location_id;
```

---

### `vw_ingredient_balance`
Остатки ингредиентов по локациям.

**Поля:**
| Колонка | Описание |
|---------|----------|
| location_id | ID локации |
| ingredient_code | Код ингредиента |
| qty_balance | Остаток |
| unit | Единица измерения |

**Логика:**
```sql
-- Остаток = Сумма загрузок - Расход по продажам
SELECT
  location_id,
  ingredient_code,
  (
    SUM(qty_loaded)  -- загрузки
    -
    COALESCE(
      (SELECT SUM(di.qty_per_unit)
       FROM vw_tx_cogs t
       JOIN drink_items di ON di.drink_id = t.drink_id
       WHERE di.ingredient_code = il.ingredient_code
         AND t.location_id = il.location_id
         AND i.expense_kind = 'stock_tracked'
      ), 0
    )  -- расход
  ) AS qty_balance
FROM ingredient_loads il
JOIN ingredients i ON i.ingredient_code = il.ingredient_code
WHERE i.expense_kind = 'stock_tracked'  -- только постоянные
GROUP BY location_id, ingredient_code;
```

---

### `vw_ingredient_usage_daily`
Ежедневный расход ингредиентов.

**Поля:**
| Колонка | Описание |
|---------|----------|
| day | День (DATE) |
| location_id | ID локации |
| ingredient_code | Код ингредиента |
| qty_used | Количество израсходовано |

---

### `vw_ingredient_alerts_v2`
Алерты по остаткам ингредиентов.

**Поля:**
| Колонка | Описание |
|---------|----------|
| location_id | ID локации |
| location_name | Название локации |
| ingredient_code | Код ингредиента |
| ingredient_name | Название ингредиента |
| unit_ru | Единица измерения (RU) |
| qty_balance | Остаток |
| alert_threshold | Порог алерта |
| days_left | Дней до окончания |
| alert_days_threshold | Порог дней |
| alert_level | Уровень алерта: LOW_STOCK, DAYS_LEFT |

**Логика:**
```sql
SELECT
  ib.*,
  ib.qty_balance / NULLIF(iad.avg_daily_used_7d, 0) AS days_left,
  CASE
    WHEN ib.qty_balance <= i.alert_threshold THEN 'LOW_STOCK'
    WHEN (ib.qty_balance / NULLIF(iad.avg_daily_used_7d, 0)) <= i.alert_days_threshold THEN 'DAYS_LEFT'
    ELSE NULL
  END AS alert_level
FROM vw_ingredient_balance ib
JOIN vw_ingredient_avg_daily_7d iad USING (location_id, ingredient_code)
JOIN ingredients i ON i.ingredient_code = ib.ingredient_code
WHERE alert_level IS NOT NULL;
```

---

### `vw_variable_expenses_daily`
Переменные расходы по дням.

**Поля:**
| Колонка | Описание |
|---------|----------|
| expense_date | Дата расхода |
| location_id | ID локации |
| total_amount_rub | Сумма за день (₽) |

**Логика:**
```sql
SELECT
  expense_date,
  location_id,
  SUM(amount_rub) AS total_amount_rub
FROM variable_expenses
GROUP BY expense_date, location_id;
```

---

### `vw_owner_report_daily`
Ежедневная сводка для отчета собственника (с чистой прибылью).

**Поля:**
| Колонка | Описание |
|---------|----------|
| day | День |
| location_id | ID локации |
| revenue_rub | Выручка (₽) |
| cogs_rub | Себестоимость (₽) |
| gross_profit_rub | Валовая прибыль (₽) |
| gross_margin_pct | Валовая маржа (%) |
| variable_expenses_rub | Переменные расходы (₽) |
| net_profit_rub | Чистая прибыль (₽) |
| net_margin_pct | Чистая маржа (%) |

**Логика:**
```sql
SELECT
  k.day,
  k.location_id,
  k.revenue_rub,
  k.cogs_rub,
  k.gross_profit_rub,
  k.gross_margin_pct,
  COALESCE(ve.total_amount_rub, 0) AS variable_expenses_rub,
  (k.gross_profit_rub - COALESCE(ve.total_amount_rub, 0)) AS net_profit_rub,
  ((k.gross_profit_rub - COALESCE(ve.total_amount_rub, 0)) / NULLIF(k.revenue_rub, 0) * 100) AS net_margin_pct
FROM vw_kpi_daily k
LEFT JOIN vw_variable_expenses_daily ve ON ve.expense_date = k.day
  AND ve.location_id = k.location_id;
```

---

## 🧮 Ключевые формулы

### 1. Себестоимость напитка (COGS per drink)
```sql
COGS = SUM(
  drink_items.qty_per_unit * ingredients.cost_per_unit_rub
)
WHERE ingredients.expense_kind = 'stock_tracked'  -- только постоянные
```

**Пример:**
```
Капучино:
  - Кофе зерно: 18г × 1.90₽/г = 34.20₽
  - Молоко: 120мл × 0.08₽/мл = 9.60₽
  COGS = 34.20₽ + 9.60₽ = 43.80₽
```

---

### 2. Валовая прибыль (Gross Profit)
```sql
Gross Profit = Revenue - COGS
```

**Пример:**
```
Выручка: 100₽
COGS: 43.80₽
Валовая прибыль = 100₽ - 43.80₽ = 56.20₽
```

---

### 3. Валовая маржа (Gross Margin %)
```sql
Gross Margin % = (Gross Profit / Revenue) × 100
```

**Пример:**
```
Валовая прибыль: 56.20₽
Выручка: 100₽
Валовая маржа = (56.20₽ / 100₽) × 100 = 56.2%
```

---

### 4. Чистая прибыль (Net Profit)
```sql
Net Profit = Gross Profit - Variable Expenses
```

**Пример:**
```
Валовая прибыль: 56.20₽ × 250 продаж = 14,050₽
Переменные расходы за день: 2,500₽
Чистая прибыль = 14,050₽ - 2,500₽ = 11,550₽
```

---

### 5. Чистая маржа (Net Margin %)
```sql
Net Margin % = (Net Profit / Revenue) × 100
```

**Пример:**
```
Чистая прибыль: 11,550₽
Выручка: 25,000₽
Чистая маржа = (11,550₽ / 25,000₽) × 100 = 46.2%
```

---

### 6. Остаток ингредиента (Balance)
```sql
Balance = SUM(loads.qty_loaded) - SUM(usage.qty_used)
WHERE ingredients.expense_kind = 'stock_tracked'
```

**Пример:**
```
Загрузки молока: 50л
Расход за период: 35л
Остаток = 50л - 35л = 15л
```

---

### 7. Дней до окончания (Days Left)
```sql
Days Left = qty_balance / avg_daily_usage_7d
```

**Пример:**
```
Остаток молока: 15л
Средний расход в день: 4л/день
Дней до окончания = 15л / 4л = 3.75 дней
```

---

## 🔍 Примеры запросов

### 1. Получить KPI за период
```sql
SELECT
  SUM(tx_count) AS total_sales,
  SUM(revenue_rub) AS total_revenue,
  SUM(cogs_rub) AS total_cogs,
  SUM(gross_profit_rub) AS total_gross_profit,
  (SUM(gross_profit_rub) / NULLIF(SUM(revenue_rub), 0) * 100) AS gross_margin_pct
FROM vw_kpi_daily
WHERE day >= '2026-01-01' AND day <= '2026-01-11'
  AND location_id = 1;
```

---

### 2. Топ-10 напитков по выручке
```sql
SELECT
  product_name,
  COUNT(*) AS tx_count,
  SUM(revenue_rub) AS total_revenue,
  SUM(gross_profit_rub) AS total_gross_profit,
  (SUM(gross_profit_rub) / NULLIF(SUM(revenue_rub), 0) * 100) AS margin_pct
FROM vw_tx_cogs
WHERE tx_time >= '2026-01-01' AND tx_time < '2026-01-12'
  AND location_id = 1
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 10;
```

---

### 3. Алерты по остаткам
```sql
SELECT
  location_name,
  ingredient_name,
  qty_balance,
  unit_ru,
  days_left,
  alert_level
FROM vw_ingredient_alerts_v2
WHERE location_id = 1
ORDER BY
  CASE alert_level
    WHEN 'LOW_STOCK' THEN 1
    WHEN 'DAYS_LEFT' THEN 2
  END,
  days_left ASC NULLS LAST;
```

---

### 4. Чистая прибыль за период
```sql
SELECT
  SUM(revenue_rub) AS revenue,
  SUM(cogs_rub) AS cogs,
  SUM(gross_profit_rub) AS gross_profit,
  SUM(variable_expenses_rub) AS variable_expenses,
  SUM(net_profit_rub) AS net_profit,
  (SUM(net_profit_rub) / NULLIF(SUM(revenue_rub), 0) * 100) AS net_margin_pct
FROM vw_owner_report_daily
WHERE day >= '2026-01-01' AND day <= '2026-01-11'
  AND location_id = 1;
```

---

## 📝 Заметки

1. **Постоянные vs Переменные ингредиенты:**
   - Постоянные (`expense_kind = 'stock_tracked'`) участвуют в остатках и COGS
   - Переменные (`expense_kind = 'not_tracked'`) только справочно в рецепте

2. **Обработка несвязанных продаж:**
   - Если `machine_item_id` не привязан к рецепту → COGS = NULL
   - Такие продажи показываются в "Что сделать" в отчете собственника

3. **Переменные расходы:**
   - Вводятся вручную оператором/собственником
   - Не автоматизированы (нет списания из остатков)

4. **Фильтры во всех экранах:**
   - Период (start_date, end_date)
   - Локация (location_id)
   - Терминал (term_id)

5. **Часовой пояс:**
   - Все timestamps в БД хранятся в UTC
   - В API и UI используется `Europe/Moscow` (или ADMIN_TIMEZONE из .env)

---

**Этот документ обновляется по мере развития проекта.**
