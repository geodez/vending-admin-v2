# Vending Admin v2 - Архитектура проекта

## 🎯 Цель проекта

Современная административная панель для управления вендинговым бизнесом с аутентификацией через Telegram и полным функционалом для:
- Собственников (полный доступ к финансам и управлению)
- Операторов (доступ к оперативному управлению)

---

## 🏗️ Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Mini App                         │
│              (React + TypeScript + Vite)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ├── Telegram WebApp API (auth)
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│   • REST API                                                 │
│   • Telegram Auth Middleware                                │
│   • Role-Based Access Control (RBAC)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                             │
│   • Пользователи и роли                                     │
│   • Данные Vendista (синхронизация)                        │
│   • Бизнес-логика (рецепты, склад, расходы)               │
└─────────────────────────────────────────────────────────────┘
                        ↑
                        │
┌───────────────────────┴─────────────────────────────────────┐
│              Vendista API (внешний источник)                │
│   • Транзакции                                              │
│   • Данные терминалов                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Аутентификация через Telegram

### Принцип работы

1. **Пользователь открывает Telegram Mini App**
   - Приложение получает `window.Telegram.WebApp.initData`
   - Данные содержат: `user.id`, `user.username`, `user.first_name`, `auth_date`, `hash`

2. **Валидация на бэкенде**
   ```python
   # FastAPI middleware проверяет:
   # 1. Подлинность данных через hash (HMAC-SHA256)
   # 2. Срок действия auth_date (не старше 24 часов)
   # 3. Наличие пользователя в базе
   ```

3. **JWT Token выдача**
   ```python
   # После успешной валидации:
   # 1. Проверяем user_id в таблице users
   # 2. Выдаем JWT token с claims: user_id, role, permissions
   # 3. Frontend сохраняет токен и использует для API запросов
   ```

### Схема БД для пользователей

```sql
-- Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    role TEXT NOT NULL DEFAULT 'operator',  -- 'owner', 'operator'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Таблица прав доступа
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,  -- 'view_sales', 'edit_recipes', etc.
    description TEXT
);

-- Связь пользователей и прав
CREATE TABLE user_permissions (
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    permission_id INT REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, permission_id)
);

-- Связь ролей и прав (предустановленные роли)
CREATE TABLE role_permissions (
    role TEXT NOT NULL,  -- 'owner', 'operator'
    permission_id INT REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role, permission_id)
);
```

### Права доступа по ролям

**Собственник (Owner)**
- ✅ Просмотр всех разделов
- ✅ Редактирование всех данных
- ✅ Просмотр финансовых отчетов
- ✅ Управление пользователями
- ✅ Настройки системы

**Оператор (Operator)**
- ✅ Просмотр: Обзор, Продажи, Склад
- ✅ Редактирование: Рецепты, Ингредиенты, Кнопки терминала
- ✅ Ввод: Переменные расходы, Загрузки склада
- ❌ Финансовые отчеты (Отчет собственника)
- ❌ Управление пользователями
- ❌ Настройки системы

---

## 🖥️ Backend Architecture (FastAPI)

### Структура проекта

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings (Pydantic Settings)
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── telegram.py           # Telegram auth validation
│   │   ├── jwt.py                # JWT token generation/validation
│   │   ├── permissions.py        # RBAC logic
│   │   └── middleware.py         # Auth middleware
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py               # API dependencies (get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py           # POST /auth/telegram
│   │       ├── overview.py       # GET /overview (дашборд)
│   │       ├── sales.py          # GET /sales/* (продажи)
│   │       ├── inventory.py      # GET/POST /inventory/* (склад)
│   │       ├── recipes.py        # GET/POST/PUT/DELETE /recipes/*
│   │       ├── ingredients.py    # GET/POST/PUT/DELETE /ingredients/*
│   │       ├── buttons.py        # GET/POST /buttons/* (кнопки терминала)
│   │       ├── expenses.py       # GET/POST /expenses/* (переменные расходы)
│   │       ├── owner_report.py   # GET /owner-report/* (отчет собственника)
│   │       └── settings.py       # GET/POST /settings/* (настройки)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # User, Permission models
│   │   ├── location.py           # Location, Terminal models
│   │   ├── product.py            # Product, Drink models
│   │   ├── ingredient.py         # Ingredient model
│   │   ├── recipe.py             # Recipe, RecipeItem models
│   │   ├── inventory.py          # IngredientLoad, Balance models
│   │   ├── expense.py            # VariableExpense model
│   │   └── transaction.py        # VendistaTx model
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py               # TelegramAuthRequest, TokenResponse
│   │   ├── user.py               # UserResponse, UserCreate
│   │   ├── overview.py           # OverviewResponse (KPIs + alerts)
│   │   ├── sales.py              # SalesResponse schemas
│   │   ├── inventory.py          # InventoryResponse schemas
│   │   ├── recipe.py             # RecipeResponse schemas
│   │   ├── ingredient.py         # IngredientResponse schemas
│   │   ├── expense.py            # ExpenseResponse schemas
│   │   └── owner_report.py       # OwnerReportResponse schemas
│   │
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py               # CRUD для пользователей
│   │   ├── location.py           # CRUD для локаций/терминалов
│   │   ├── ingredient.py         # CRUD для ингредиентов
│   │   ├── recipe.py             # CRUD для рецептов
│   │   ├── inventory.py          # CRUD для склада
│   │   ├── expense.py            # CRUD для расходов
│   │   └── transaction.py        # CRUD для транзакций
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py            # SQLAlchemy session
│   │   └── base.py               # Base model
│   │
│   └── services/
│       ├── __init__.py
│       ├── vendista_sync.py      # Синхронизация с Vendista API
│       ├── kpi_calculator.py     # Расчет KPI и метрик
│       └── alert_service.py      # Генерация алертов
│
├── migrations/                    # Alembic migrations
├── tests/
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### API Endpoints

```
POST   /api/v1/auth/telegram          # Аутентификация
GET    /api/v1/auth/me                # Текущий пользователь

# Обзор (Dashboard)
GET    /api/v1/overview               # KPIs + Alerts
GET    /api/v1/overview/alerts        # Список алертов

# Продажи
GET    /api/v1/sales/summary          # Сводка продаж
GET    /api/v1/sales/daily            # По дням
GET    /api/v1/sales/by-product       # По напиткам
GET    /api/v1/sales/margin           # Маржинальность

# Склад
GET    /api/v1/inventory/balances     # Остатки
GET    /api/v1/inventory/usage        # Расход
GET    /api/v1/inventory/loads        # Загрузки
POST   /api/v1/inventory/loads        # Добавить загрузку
GET    /api/v1/inventory/alerts       # Алерты по остаткам

# Рецепты
GET    /api/v1/recipes                # Список рецептов
POST   /api/v1/recipes                # Создать рецепт
GET    /api/v1/recipes/{id}           # Детали рецепта
PUT    /api/v1/recipes/{id}           # Обновить рецепт
DELETE /api/v1/recipes/{id}           # Удалить рецепт
POST   /api/v1/recipes/{id}/clone     # Клонировать в другую локацию

# Ингредиенты
GET    /api/v1/ingredients            # Список ингредиентов
POST   /api/v1/ingredients            # Создать ингредиент
GET    /api/v1/ingredients/{id}       # Детали ингредиента
PUT    /api/v1/ingredients/{id}       # Обновить ингредиент
DELETE /api/v1/ingredients/{id}       # Удалить ингредиент

# Кнопки терминала
GET    /api/v1/buttons                # Список привязок
POST   /api/v1/buttons/map            # Привязать кнопку к рецепту
POST   /api/v1/buttons/batch-map      # Массовая привязка
POST   /api/v1/buttons/clone          # Копирование между локациями

# Переменные расходы
GET    /api/v1/expenses               # Список расходов
POST   /api/v1/expenses               # Добавить расход
GET    /api/v1/expenses/analytics     # Аналитика по расходам
GET    /api/v1/expenses/categories    # Справочник категорий

# Отчет собственника (Owner only)
GET    /api/v1/owner-report/summary   # Сводка
GET    /api/v1/owner-report/daily     # По дням
GET    /api/v1/owner-report/issues    # Список проблем

# Настройки (Owner only)
GET    /api/v1/settings/users         # Список пользователей
POST   /api/v1/settings/users         # Создать пользователя
PUT    /api/v1/settings/users/{id}    # Обновить пользователя
GET    /api/v1/settings/locations     # Локации и терминалы
POST   /api/v1/settings/mappings      # Маппинг терминалов
```

---

## 🎨 Frontend Architecture (React + TypeScript)

### Технологический стек

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **State Management:** Zustand (легковесная альтернатива Redux)
- **API Client:** Axios
- **UI Library:** Ant Design (или Mantine)
- **Charts:** Recharts или Apache ECharts
- **Forms:** React Hook Form + Zod validation
- **Telegram SDK:** @twa-dev/sdk

### Структура проекта

```
frontend/
├── public/
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component
│   ├── vite-env.d.ts
│   │
│   ├── api/
│   │   ├── client.ts              # Axios instance with interceptors
│   │   ├── auth.ts                # Auth API calls
│   │   ├── overview.ts            # Overview API
│   │   ├── sales.ts               # Sales API
│   │   ├── inventory.ts           # Inventory API
│   │   ├── recipes.ts             # Recipes API
│   │   ├── ingredients.ts         # Ingredients API
│   │   ├── buttons.ts             # Buttons API
│   │   ├── expenses.ts            # Expenses API
│   │   └── ownerReport.ts         # Owner Report API
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx      # Основной layout
│   │   │   ├── Sidebar.tsx        # Боковая панель
│   │   │   ├── Header.tsx         # Шапка с фильтрами
│   │   │   └── TabBar.tsx         # Нижняя навигация (мобильная)
│   │   │
│   │   ├── common/
│   │   │   ├── Card.tsx           # Карточка
│   │   │   ├── Alert.tsx          # Алерт
│   │   │   ├── Button.tsx         # Кнопка
│   │   │   ├── DateRangePicker.tsx # Выбор периода
│   │   │   ├── LocationSelect.tsx # Выбор локации
│   │   │   └── Loading.tsx        # Индикатор загрузки
│   │   │
│   │   ├── charts/
│   │   │   ├── LineChart.tsx      # График линейный
│   │   │   ├── BarChart.tsx       # График столбцы
│   │   │   └── PieChart.tsx       # График круговой
│   │   │
│   │   └── features/
│   │       ├── RecipeForm.tsx     # Форма рецепта
│   │       ├── IngredientForm.tsx # Форма ингредиента
│   │       ├── ExpenseForm.tsx    # Форма расхода
│   │       └── ButtonMapping.tsx  # Привязка кнопок
│   │
│   ├── pages/
│   │   ├── LoginPage.tsx          # Страница логина (Telegram auth)
│   │   ├── OverviewPage.tsx       # 1. Обзор
│   │   ├── SalesPage.tsx          # 2. Продажи
│   │   ├── InventoryPage.tsx      # 3. Склад
│   │   ├── RecipesPage.tsx        # 4. Рецепты
│   │   ├── IngredientsPage.tsx    # 5. Ингредиенты
│   │   ├── ButtonsPage.tsx        # 6. Кнопки терминала
│   │   ├── ExpensesPage.tsx       # 7. Переменные расходы
│   │   ├── OwnerReportPage.tsx    # 8. Отчет собственника
│   │   └── SettingsPage.tsx       # 9. Настройки
│   │
│   ├── store/
│   │   ├── authStore.ts           # Auth state (user, token, role)
│   │   ├── filtersStore.ts        # Фильтры (период, локация)
│   │   └── uiStore.ts             # UI state (sidebar open, etc.)
│   │
│   ├── hooks/
│   │   ├── useAuth.ts             # Auth hook
│   │   ├── useTelegram.ts         # Telegram WebApp hook
│   │   ├── usePermissions.ts      # Проверка прав
│   │   └── useFilters.ts          # Фильтры hook
│   │
│   ├── types/
│   │   ├── api.ts                 # API типы
│   │   ├── models.ts              # Модели данных
│   │   └── telegram.ts            # Telegram типы
│   │
│   ├── utils/
│   │   ├── formatters.ts          # Форматирование (дата, число, валюта)
│   │   ├── validators.ts          # Валидация
│   │   └── constants.ts           # Константы
│   │
│   └── styles/
│       ├── global.css             # Глобальные стили
│       └── theme.ts               # Тема (цвета, шрифты)
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.example
```

---

## 📱 Экраны админ-панели

### 1. **Экран "Обзор" (Overview)**

**Компоненты:**
- KPI карточки (за выбранный период):
  - Выручка (₽)
  - Количество продаж
  - Валовая прибыль (₽)
  - Валовая маржа (%)
  - Переменные расходы (₽)
  - Чистая прибыль (₽)
  - Чистая маржа (%)
  
- График: Выручка и прибыль по дням
- Список критических алертов (остатки на складе)
- Краткая статистика по локациям

**Права доступа:** Owner ✅, Operator ✅

---

### 2. **Экран "Продажи" (Sales)**

**Компоненты:**
- Графики:
  - Выручка по дням
  - Валовая прибыль по дням
  
- Таблица продаж по напиткам:
  | Напиток | Кол-во | Выручка | Себестоимость | Валовая прибыль | Маржа % |
  |---------|--------|---------|---------------|-----------------|---------|
  | Капучино | 250 | 25,000₽ | 8,500₽ | 16,500₽ | 66% |
  | Латте | 180 | 21,600₽ | 7,200₽ | 14,400₽ | 67% |
  | Эспрессо | 320 | 16,000₽ | 4,800₽ | 11,200₽ | 70% |
  
- Фильтры:
  - Период (дни, недели, месяцы)
  - Локация
  - Терминал

**Права доступа:** Owner ✅, Operator ✅

---

### 3. **Экран "Склад" (Inventory)**

**Вкладки:**

**3.1. Остатки**
- Таблица остатков:
  | Ингредиент | Остаток | Ед.изм. | Расход/день | Осталось дней | Статус |
  |------------|---------|---------|-------------|---------------|--------|
  | Кофе зерно | 5.2 кг | кг | 0.8 кг | 6 дней | 🟡 Предупреждение |
  | Молоко | 12 л | л | 3.5 л | 3 дня | 🔴 Критично |
  
**3.2. Пополнения**
- Список загрузок (последние 50):
  | Дата | Локация | Ингредиент | Количество | Комментарий |
  |------|---------|------------|------------|-------------|
  | 11.01.2026 | Островского | Кофе зерно | 10 кг | Закупка недели |
  
- Кнопка "Добавить загрузку"

**3.3. Расход по дням**
- График расхода ингредиентов по дням
- Выбор ингредиента для детализации

**Права доступа:** Owner ✅, Operator ✅

---

### 4. **Экран "Рецепты" (Recipes)**

**Компоненты:**
- Список рецептов по локации:
  | Рецепт | Локация | Себестоимость | Ингредиенты | Статус |
  |--------|---------|---------------|-------------|--------|
  | Капучино | Островского | 34₽ | Кофе, Молоко | ✅ Активен |
  | Латте | Островского | 40₽ | Кофе, Молоко | ✅ Активен |
  
- Кнопка "Добавить рецепт"
- Кнопка "Клонировать в другую локацию"

**Форма рецепта:**
```
Название: [________]
Локация: [Dropdown]
Привязка к продукту: [Dropdown]

Состав рецепта:
┌─────────────────────────────────────────────┐
│ Ингредиент     | Кол-во | Ед.изм. | [x]    │
├─────────────────────────────────────────────┤
│ Кофе зерно     | 18     | г       | [x]    │
│ Молоко         | 120    | мл      | [x]    │
└─────────────────────────────────────────────┘

[+ Добавить ингредиент]

Себестоимость порции: 34₽

[Сохранить] [Отмена]
```

**Права доступа:** Owner ✅, Operator ✅

---

### 5. **Экран "Ингредиенты" (Ingredients)**

**Компоненты:**
- Справочник ингредиентов:
  | Код | Название | Тип расхода | Ед.изм. | Упаковка | Цена за ед. | Статус |
  |-----|----------|-------------|---------|----------|-------------|--------|
  | COFFEE_BEANS | Кофе зерно | Постоянный | г | 1000 г | 1.9₽/г | ✅ Активен |
  | MILK | Молоко | Постоянный | мл | 1000 мл | 0.08₽/мл | ✅ Активен |
  | SUGAR | Сахар | Переменный | г | 1000 г | 0.05₽/г | ✅ Активен |
  
- Кнопка "Добавить ингредиент"

**Форма ингредиента:**
```
Код: [________]
Название: [________]
Название (RU): [________]

Тип расхода:
  ○ Постоянный (участвует в остатках и себестоимости)
  ○ Переменный (только справочно)

Единица измерения: [Dropdown: г, мл, шт]
Единица (RU): [________]

Упаковка:
  Количество в упаковке: [____] [ед.изм.]
  Цена упаковки: [____] ₽

Расчетная цена за единицу: 1.9 ₽

Пороги алертов:
  Минимальный остаток: [____] [ед.изм.]
  Минимум дней до окончания: [____] дней

[Сохранить] [Отмена]
```

**Права доступа:** Owner ✅, Operator ✅

---

### 6. **Экран "Кнопки терминала" (Buttons Mapping)**

**Компоненты:**
- Выбор локации и терминала
- Таблица кнопок терминала:
  | Machine Item ID | Продукт (Vendista) | Рецепт | Статус |
  |-----------------|---------------------|---------|--------|
  | 1 | Капучино 0.2л | Капучино | ✅ Привязан |
  | 2 | Латте 0.3л | Латте | ✅ Привязан |
  | 3 | Эспрессо | — | ⚠️ Не привязан |
  | 4 | Американо | Американо | ✅ Привязан |
  
- Кнопки:
  - "Привязать по шаблону" (массовая привязка по названиям)
  - "Копировать из другой локации"

**Форма привязки:**
```
Machine Item ID: 3
Продукт (Vendista): Эспрессо

Выберите рецепт:
[Dropdown: список рецептов локации]

[Привязать] [Отмена]
```

**Права доступа:** Owner ✅, Operator ✅

---

### 7. **Экран "Переменные расходы" (Variable Expenses)**

**Вкладки:**

**7.1. Список расходов**
- Таблица расходов:
  | Дата | Локация | Терминал | Категория | Сумма | Комментарий |
  |------|---------|----------|-----------|-------|-------------|
  | 10.01 | Островского | Терм. #1 | Аренда | 15,000₽ | Месячная |
  | 09.01 | Островского | — | Транспорт | 2,500₽ | Доставка |
  
- Кнопка "Добавить расход"

**7.2. Аналитика**
- График расходов по дням
- График по категориям (pie chart)
- Сравнение между локациями

**Форма расхода:**
```
Дата: [Datepicker]
Локация: [Dropdown]
Терминал: [Dropdown (опционально)]

Категория: [Dropdown]
  - Аренда
  - Транспорт
  - Обслуживание
  - Салфетки/стаканы
  - Прочее

Сумма: [____] ₽
Комментарий: [________]

[Создан пользователем]: Ivan Ivanov

[Сохранить] [Отмена]
```

**Права доступа:** Owner ✅, Operator ✅

---

### 8. **Экран "Отчет собственника" (Owner Report)**

**Компоненты:**

**8.1. Основные метрики (за период)**
- KPI карточки:
  - Выручка (₽)
  - Кол-во продаж
  - Средний чек (₽)
  - COGS (себестоимость постоянных ингредиентов) (₽)
  - Валовая прибыль (₽)
  - Валовая маржа (%)
  - Переменные расходы (₽)
  - Чистая прибыль (₽)
  - Чистая маржа (%)

**8.2. Табличная часть**

Вкладки:
- По дням
- По напиткам
- По локациям
- По терминалам

Пример таблицы "По дням":
| Дата | Выручка | COGS | Валовая прибыль | Переменные расходы | Чистая прибыль | Чистая маржа % |
|------|---------|------|-----------------|---------------------|----------------|----------------|
| 11.01 | 45,000₽ | 15,000₽ | 30,000₽ | 5,000₽ | 25,000₽ | 56% |
| 10.01 | 42,000₽ | 14,000₽ | 28,000₽ | 3,500₽ | 24,500₽ | 58% |

**8.3. Блок "Что сделать" (Issues)**
- Несвязанные Machine Item ID (продажи без рецепта):
  ```
  ⚠️ Терминал #178428, Machine Item 5: 25 продаж за период
      Продукт: "Капучино XL"
      Действие: [Привязать к рецепту]
  ```

- Ингредиенты без себестоимости:
  ```
  ⚠️ Ингредиент "Сироп ваниль": отсутствует цена упаковки
      Действие: [Добавить цену]
  ```

- Критичные остатки:
  ```
  🔴 Молоко: осталось 2.5 л (< 3 дней)
      Локация: Островского
      Действие: [Добавить загрузку]
  ```

**Права доступа:** Owner ✅, Operator ❌

---

### 9. **Экран "Настройки" (Settings)**

**Вкладки:**

**9.1. Пользователи**
- Список пользователей:
  | Telegram ID | Имя | Роль | Статус | Дата добавления |
  |-------------|-----|------|--------|-----------------|
  | 123456789 | Ivan Ivanov | Owner | ✅ Активен | 01.01.2026 |
  | 987654321 | Petr Petrov | Operator | ✅ Активен | 05.01.2026 |
  
- Кнопка "Добавить пользователя"

**9.2. Категории расходов**
- Справочник категорий переменных расходов
- Возможность добавления/редактирования

**9.3. Маппинг локаций/терминалов**
- Таблица терминалов:
  | Terminal ID | Terminal Comment (Vendista) | Имя вручную | Локация |
  |-------------|------------------------------|-------------|---------|
  | 145912 | Островского Терм#1 | — | Островского |
  | 178428 | ЦУМ Точка2 | ЦУМ 2-й этаж | ЦУМ |
  
- Приоритет отображения:
  1. Имя вручную (если задано)
  2. Terminal Comment
  3. Fallback: "Терминал #[ID]"

**Права доступа:** Owner ✅, Operator ❌

---

## 🔄 Ключевые бизнес-правила

### Расчет остатков склада
```python
# Остаток = Сумма загрузок - Расход по продажам (только по постоянным ингредиентам)

balance = (
    SELECT SUM(qty_loaded) FROM ingredient_loads WHERE ingredient_code = ?
) - (
    SELECT SUM(recipe_items.qty_per_unit * tx_count)
    FROM transactions
    JOIN recipes ON recipes.product_external_id = transactions.product_id
    JOIN recipe_items ON recipe_items.drink_id = recipes.drink_id
    WHERE recipe_items.ingredient_code = ?
      AND ingredients.expense_kind = 'stock_tracked'  -- только постоянные
)
```

### Расчет себестоимости напитка (COGS)
```python
# Себестоимость = Сумма (количество ингредиента × цена за единицу)
# Только постоянные ингредиенты (expense_kind = 'stock_tracked')

cogs_per_drink = SUM(
    recipe_items.qty_per_unit * ingredients.unit_cost_rub
    WHERE ingredients.expense_kind = 'stock_tracked'
)
```

### Расчет чистой прибыли
```python
# Валовая прибыль = Выручка - COGS (себестоимость постоянных ингредиентов)
gross_profit = revenue - cogs

# Чистая прибыль = Валовая прибыль - Переменные расходы
net_profit = gross_profit - variable_expenses

# Чистая маржа = (Чистая прибыль / Выручка) × 100%
net_margin_pct = (net_profit / revenue) * 100
```

### Обработка напитков без рецепта
```python
# Если у напитка нет рецепта:
# 1. Помечаем как "без рецепта" в отчетах
# 2. COGS = 0 (или null)
# 3. Маржинальность = null (не считается)
# 4. Добавляем в список проблем "Что сделать"
```

### Алерты по остаткам
```python
# Критичный алерт:
if qty_balance <= alert_threshold:
    alert_level = 'LOW_STOCK'
    
# Предупреждение:
if days_left <= alert_days_threshold:
    alert_level = 'DAYS_LEFT'
    
# Расчет дней до окончания:
days_left = qty_balance / avg_daily_usage_7d
```

---

## 🚀 План разработки (Этапы)

### **Этап 1: Инфраструктура и аутентификация** (1 неделя)

✅ Задачи:
1. Создать GitHub репозиторий `vending-admin-v2`
2. Настроить Backend (FastAPI):
   - Структура проекта
   - Docker + PostgreSQL
   - Alembic migrations
3. Реализовать Telegram Auth:
   - Middleware для валидации initData
   - JWT токены
   - Таблица `users` и RBAC
4. Настроить Frontend (React + Vite):
   - Структура проекта
   - Telegram Mini App SDK
   - Axios client с interceptors
5. Базовый LoginPage с Telegram auth

**Результат:** Работающая аутентификация через Telegram, JWT токены, роли Owner/Operator

---

### **Этап 2: Синхронизация с Vendista API** (3-4 дня)

✅ Задачи:
1. Перенести логику синхронизации из старого проекта:
   - `vendista_terminals`
   - `vendista_tx_raw`
   - `sync_state`
2. Создать сервис `VendistaSync` для автоматической синхронизации
3. Настроить cron-задачу для регулярной синхронизации

**Результат:** Данные Vendista автоматически синхронизируются в новую БД

---

### **Этап 3: Основные сущности и CRUD** (1 неделя)

✅ Задачи:
1. Создать модели и миграции:
   - `locations`, `terminals`
   - `products`, `drinks`
   - `ingredients`
   - `recipes`, `drink_items` (состав рецепта)
   - `location_drink_map` (привязки)
2. Реализовать CRUD API для:
   - Ингредиентов
   - Рецептов
   - Привязок кнопок
3. Создать UI:
   - Страница "Ингредиенты" (список + форма)
   - Страница "Рецепты" (список + форма)
   - Страница "Кнопки терминала"

**Результат:** Можно создавать и редактировать ингредиенты, рецепты, привязывать кнопки

---

### **Этап 4: Склад и загрузки** (3-4 дня)

✅ Задачи:
1. Таблицы:
   - `ingredient_loads` (загрузки)
2. Представления:
   - `vw_ingredient_balance` (остатки)
   - `vw_ingredient_usage_daily` (расход по дням)
   - `vw_ingredient_alerts` (алерты)
3. API эндпоинты для склада
4. UI страница "Склад":
   - Вкладка "Остатки"
   - Вкладка "Пополнения" + форма загрузки
   - Вкладка "Расход по дням"

**Результат:** Работающая система учета склада с остатками и алертами

---

### **Этап 5: Продажи и KPI** (1 неделя)

✅ Задачи:
1. Представления:
   - `vw_tx_cogs` (COGS и валовая прибыль по транзакциям)
   - `vw_kpi_daily` (KPI по дням)
   - `vw_kpi_product` (KPI по напиткам)
2. API эндпоинты для продаж
3. UI страница "Продажи":
   - Графики (выручка, прибыль)
   - Таблица по напиткам
4. UI страница "Обзор":
   - KPI карточки
   - График
   - Алерты

**Результат:** Дашборд с KPI и страница продаж с аналитикой

---

### **Этап 6: Переменные расходы** (2-3 дня)

✅ Задачи:
1. Таблицы:
   - `variable_expenses`
   - `expense_categories`
2. Представления:
   - `vw_variable_expenses_daily`
   - `vw_variable_expenses_by_category`
3. API эндпоинты для расходов
4. UI страница "Переменные расходы":
   - Список + форма добавления
   - Вкладка "Аналитика" с графиками

**Результат:** Можно вводить переменные расходы и анализировать их

---

### **Этап 7: Отчет собственника** (3-4 дня)

✅ Задачи:
1. Представления:
   - `vw_owner_report_daily` (ежедневная сводка с чистой прибылью)
   - `vw_owner_report_issues` (список проблем)
2. API эндпоинты для отчета собственника
3. UI страница "Отчет собственника":
   - KPI карточки (с чистой прибылью)
   - Таблицы (по дням/напиткам/локациям)
   - Блок "Что сделать" (проблемы)

**Результат:** Полный отчет собственника с чистой прибылью и списком проблем

---

### **Этап 8: Настройки и администрирование** (2-3 дня)

✅ Задачи:
1. API эндпоинты:
   - Управление пользователями
   - Категории расходов
   - Маппинг терминалов
2. UI страница "Настройки":
   - Вкладка "Пользователи"
   - Вкладка "Категории расходов"
   - Вкладка "Терминалы"

**Результат:** Owner может управлять пользователями и настройками системы

---

### **Этап 9: Тестирование и деплой** (1 неделя)

✅ Задачи:
1. Написать тесты:
   - Unit tests для CRUD
   - Integration tests для API
   - E2E tests для критичных флоу
2. Настроить CI/CD (GitHub Actions):
   - Автоматические тесты
   - Деплой на production
3. Документация:
   - README.md
   - API документация (OpenAPI/Swagger)
   - Инструкция по деплою
4. Деплой на production сервер

**Результат:** Готовый production-ready продукт

---

## 📊 Итоговый функционал

### Для **Собственника** (Owner):
✅ Полный контроль над бизнесом:
- Видит все финансовые метрики (выручка, маржа, чистая прибыль)
- Управляет пользователями и их правами
- Настраивает систему (категории расходов, маппинг терминалов)
- Получает список проблем для решения (несвязанные продажи, критичные остатки)
- Анализирует эффективность по локациям и напиткам

### Для **Оператора** (Operator):
✅ Оперативное управление:
- Создает и редактирует рецепты
- Управляет ингредиентами (добавление, редактирование себестоимости)
- Привязывает кнопки терминалов к рецептам
- Вводит загрузки склада
- Вводит переменные расходы
- Видит текущие продажи и остатки

### Общие возможности:
✅ Современный UX:
- Telegram Mini App (нативное ощущение в Telegram)
- Адаптивный дизайн (десктоп + мобильная версия)
- Быстрая загрузка данных
- Интерактивные графики (ECharts)
- Фильтры (период, локация, терминал)
- Темная/светлая тема (следуя Telegram)

---

## 🔧 Технические детали

### Backend Stack
- **Python 3.12+**
- **FastAPI** (async/await, высокая производительность)
- **SQLAlchemy 2.0** (ORM)
- **Alembic** (миграции)
- **PostgreSQL 16**
- **Pydantic** (валидация данных)
- **python-jose** (JWT токены)
- **httpx** (async HTTP client для Vendista API)

### Frontend Stack
- **React 18** + **TypeScript 5**
- **Vite** (быстрый build)
- **React Router v6** (роутинг)
- **Zustand** (state management)
- **Ant Design** или **Mantine** (UI компоненты)
- **Recharts** или **ECharts** (графики)
- **React Hook Form** + **Zod** (формы)
- **Axios** (HTTP client)
- **@twa-dev/sdk** (Telegram WebApp SDK)

### DevOps
- **Docker** + **Docker Compose**
- **GitHub Actions** (CI/CD)
- **Caddy** (reverse proxy)
- **systemd** (управление сервисами)

---

## 🎯 Ключевые преимущества новой архитектуры

1. ✅ **Современная аутентификация** через Telegram (без паролей, безопасно)
2. ✅ **Role-Based Access Control** (гибкое управление правами)
3. ✅ **Чистая архитектура** (легко расширять и поддерживать)
4. ✅ **TypeScript** на фронтенде (меньше багов, лучший DX)
5. ✅ **Telegram Mini App** (нативное ощущение, не нужна установка)
6. ✅ **Production-ready** (тесты, CI/CD, мониторинг)
7. ✅ **Полная документация** (API, README, инструкции)

---

## 📝 Следующие шаги

1. ✅ Создать репозиторий на GitHub
2. ✅ Утвердить архитектуру с заказчиком
3. ✅ Начать разработку с Этапа 1 (Инфраструктура)
4. ✅ Настроить старый проект как справочник (read-only)

---

**Автор:** AI Developer (Claude)  
**Дата:** 12.01.2026  
**Версия:** 1.0
