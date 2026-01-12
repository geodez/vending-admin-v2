// API Types for Vending Admin v2

export interface User {
  id: number;
  telegram_user_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  role: 'owner' | 'operator';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TelegramAuthRequest {
  init_data: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiError {
  detail: string;
}

// Overview / Dashboard
export interface KPIMetrics {
  revenue: number;
  sales_count: number;
  gross_profit: number;
  gross_margin_pct: number;
  variable_expenses: number;
  net_profit: number;
  net_margin_pct: number;
}

export interface Alert {
  id: string;
  type: 'low_stock' | 'days_left' | 'no_recipe' | 'no_cost';
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  action_url?: string;
  created_at: string;
}

// Sales
export interface SalesByProduct {
  product_name: string;
  quantity: number;
  revenue: number;
  cogs: number;
  gross_profit: number;
  margin_pct: number;
}

// Inventory
export interface IngredientBalance {
  ingredient_code: string;
  ingredient_name: string;
  balance: number;
  unit: string;
  daily_usage_avg: number;
  days_left: number;
  status: 'ok' | 'warning' | 'critical';
}

export interface IngredientLoad {
  id: number;
  date: string;
  location_id: number;
  location_name: string;
  ingredient_code: string;
  ingredient_name: string;
  quantity: number;
  unit: string;
  comment: string | null;
  created_by_user_id: number;
  created_at: string;
}

// Recipes
export interface Recipe {
  id: number;
  drink_id: number;
  drink_name: string;
  location_id: number;
  location_name: string;
  product_external_id: string | null;
  cogs_per_unit: number;
  is_active: boolean;
  items: RecipeItem[];
}

export interface RecipeItem {
  id: number;
  ingredient_code: string;
  ingredient_name: string;
  qty_per_unit: number;
  unit: string;
  cost_per_unit: number;
}

// Ingredients
export interface Ingredient {
  code: string;
  name: string;
  name_ru: string;
  expense_kind: 'stock_tracked' | 'variable';
  unit: string;
  unit_ru: string;
  pkg_qty: number;
  pkg_cost_rub: number;
  unit_cost_rub: number;
  alert_threshold_qty: number | null;
  alert_threshold_days: number | null;
  is_active: boolean;
}

// Variable Expenses
export interface VariableExpense {
  id: number;
  date: string;
  location_id: number | null;
  location_name: string | null;
  terminal_id: number | null;
  terminal_name: string | null;
  category: string;
  amount: number;
  comment: string | null;
  created_by_user_id: number;
  created_at: string;
}

// Owner Report
export interface OwnerReportDaily {
  date: string;
  revenue: number;
  cogs: number;
  gross_profit: number;
  variable_expenses: number;
  net_profit: number;
  net_margin_pct: number;
}

export interface OwnerReportIssue {
  type: 'unmapped_product' | 'no_cost_ingredient' | 'low_stock';
  severity: 'critical' | 'warning';
  title: string;
  description: string;
  action_url: string;
  count?: number;
}
