/**
 * API module for analytics and KPI data
 */
import apiClient from './client';
import type {
  KPIData,
  SalesData,
  InventoryData,
  ExpenseData
} from '@/types/api';

// Overview KPIs
export const getKPIData = (params?: { from_date?: string; to_date?: string }) =>
  apiClient.get<KPIData>('/api/v1/analytics/kpi', { params });

// Sales
export const getSalesData = (params?: { from_date?: string; to_date?: string; location_id?: number }) =>
  apiClient.get<SalesData[]>('/api/v1/analytics/sales', { params });

export const getSalesByProduct = (params?: { from_date?: string; to_date?: string }) =>
  apiClient.get<any[]>('/api/v1/analytics/sales/by-product', { params });

export const getSalesByDrink = (params?: { from_date?: string; to_date?: string }) =>
  apiClient.get<any[]>('/api/v1/analytics/sales/by-drink', { params });

// Inventory
export const getInventoryData = () =>
  apiClient.get<InventoryData[]>('/api/v1/analytics/inventory');

export const getStockLevels = () =>
  apiClient.get<any[]>('/api/v1/analytics/inventory/stock-levels');

// Expenses
export const getVariableExpenses = (params?: { from_date?: string; to_date?: string }) =>
  apiClient.get<ExpenseData[]>('/api/v1/analytics/expenses', { params });

export const createExpense = (data: { date: string; category: string; amount: number; description?: string }) =>
  apiClient.post<ExpenseData>('/api/v1/analytics/expenses', data);

// Owner Report
export const getOwnerReport = (params?: { from_date?: string; to_date?: string }) =>
  apiClient.get<any>('/api/v1/analytics/owner-report', { params });
