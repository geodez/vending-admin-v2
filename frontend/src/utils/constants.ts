// Constants for Vending Admin v2

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
export const TELEGRAM_BOT_USERNAME = import.meta.env.VITE_TELEGRAM_BOT_USERNAME || 'coffeekznebot';

export const TOKEN_STORAGE_KEY = 'vending_admin_token';
export const USER_STORAGE_KEY = 'vending_admin_user';

export const ROLES = {
  OWNER: 'owner',
  OPERATOR: 'operator',
} as const;

export const EXPENSE_CATEGORIES = [
  'Аренда',
  'Транспорт',
  'Обслуживание',
  'Салфетки/стаканы',
  'Прочее',
] as const;

export const ALERT_TYPES = {
  LOW_STOCK: 'low_stock',
  DAYS_LEFT: 'days_left',
  NO_RECIPE: 'no_recipe',
  NO_COST: 'no_cost',
} as const;

export const ALERT_SEVERITY = {
  CRITICAL: 'critical',
  WARNING: 'warning',
  INFO: 'info',
} as const;

export const DATE_FORMAT = 'DD.MM.YYYY';
export const DATETIME_FORMAT = 'DD.MM.YYYY HH:mm';
export const TIME_FORMAT = 'HH:mm';

export const ROUTES = {
  LOGIN: '/login',
  OVERVIEW: '/',
  SALES: '/sales',
  INVENTORY: '/inventory',
  RECIPES: '/recipes',
  INGREDIENTS: '/ingredients',
  BUTTONS: '/buttons',
  MATRIX_TEMPLATES: '/matrix-templates',
  EXPENSES: '/expenses',
  OWNER_REPORT: '/owner-report',
  SETTINGS: '/settings',
} as const;

export const NAV_ITEMS = [
  {
    key: 'overview',
    label: 'Обзор',
    path: ROUTES.OVERVIEW,
    icon: 'DashboardOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'sales',
    label: 'Продажи',
    path: ROUTES.SALES,
    icon: 'LineChartOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'inventory',
    label: 'Склад',
    path: ROUTES.INVENTORY,
    icon: 'InboxOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'recipes',
    label: 'Рецепты',
    path: ROUTES.RECIPES,
    icon: 'CoffeeOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'ingredients',
    label: 'Ингредиенты',
    path: ROUTES.INGREDIENTS,
    icon: 'ShoppingOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'buttons',
    label: 'Кнопки',
    path: ROUTES.BUTTONS,
    icon: 'AppstoreOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'matrix-templates',
    label: 'Шаблоны матриц',
    path: ROUTES.MATRIX_TEMPLATES,
    icon: 'AppstoreOutlined',
    roles: ['owner'],
  },
  {
    key: 'expenses',
    label: 'Расходы',
    path: ROUTES.EXPENSES,
    icon: 'WalletOutlined',
    roles: ['owner', 'operator'],
  },
  {
    key: 'owner-report',
    label: 'Отчёт собственника',
    path: ROUTES.OWNER_REPORT,
    icon: 'FileTextOutlined',
    roles: ['owner'],
  },
  {
    key: 'settings',
    label: 'Настройки',
    path: ROUTES.SETTINGS,
    icon: 'SettingOutlined',
    roles: ['owner'],
  },
] as const;
