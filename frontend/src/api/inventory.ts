import apiClient from './client';
import type { IngredientBalance, IngredientLoad } from '@/types/api';

export interface IngredientLoadCreate {
  ingredient_code: string;
  location_id: number;
  load_date: string; // YYYY-MM-DD
  qty: number;
  unit: string;
  comment?: string;
}

export interface IngredientLoadResponse {
  id: number;
  ingredient_code: string;
  location_id: number;
  load_date: string;
  qty: number;
  unit: string;
  comment: string | null;
  created_at: string;
  created_by_user_id: number | null;
}

export interface InventoryBalanceResponse {
  ingredient_code: string;
  display_name_ru: string;
  unit: string;
  unit_ru: string;
  cost_per_unit_rub: number | null;
  alert_threshold: number | null;
  alert_days_threshold: number | null;
  location_id: number;
  location_name: string;
  total_loaded: number;
  total_used: number;
  balance: number;
  is_low_stock: boolean;
}

export interface IngredientUsageDaily {
  day: string; // YYYY-MM-DD
  location_id: number;
  location_name: string;
  ingredient_code: string;
  ingredient_name: string;
  qty_used: number;
  unit: string;
}

export const inventoryApi = {
  // Получить остатки ингредиентов
  getInventoryBalance: async (locationId?: number): Promise<InventoryBalanceResponse[]> => {
    const params = locationId ? { location_id: locationId } : {};
    const response = await apiClient.get<InventoryBalanceResponse[]>('/analytics/inventory/balance', { params });
    return response.data;
  },

  // Получить историю загрузок
  getIngredientLoads: async (params?: {
    ingredient_code?: string;
    location_id?: number;
    from_date?: string;
    to_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<IngredientLoadResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.ingredient_code) queryParams.append('ingredient_code', params.ingredient_code);
    if (params?.location_id !== undefined) queryParams.append('location_id', String(params.location_id));
    if (params?.from_date) queryParams.append('from_date', params.from_date);
    if (params?.to_date) queryParams.append('to_date', params.to_date);
    if (params?.skip !== undefined) queryParams.append('skip', String(params.skip));
    if (params?.limit !== undefined) queryParams.append('limit', String(params.limit));
    
    const response = await apiClient.get<IngredientLoadResponse[]>(`/business/ingredient-loads?${queryParams.toString()}`);
    return response.data;
  },

  // Создать загрузку ингредиента
  createIngredientLoad: async (data: IngredientLoadCreate): Promise<IngredientLoadResponse> => {
    const response = await apiClient.post<IngredientLoadResponse>('/business/ingredient-loads', data);
    return response.data;
  },

  // Получить статус инвентаря (отчет)
  getInventoryStatus: async (params?: {
    ingredient_code?: string;
    location_id?: number;
    days_back?: number;
  }): Promise<any> => {
    const queryParams = new URLSearchParams();
    if (params?.ingredient_code) queryParams.append('ingredient_code', params.ingredient_code);
    if (params?.location_id !== undefined) queryParams.append('location_id', String(params.location_id));
    if (params?.days_back !== undefined) queryParams.append('days_back', String(params.days_back));
    
    const response = await apiClient.get(`/business/inventory/status?${queryParams.toString()}`);
    return response.data;
  },

  // Получить ежедневный расход ингредиентов
  getIngredientUsageDaily: async (params?: {
    from_date?: string;
    to_date?: string;
    location_id?: number;
    ingredient_code?: string;
  }): Promise<IngredientUsageDaily[]> => {
    const queryParams = new URLSearchParams();
    if (params?.from_date) queryParams.append('from_date', params.from_date);
    if (params?.to_date) queryParams.append('to_date', params.to_date);
    if (params?.location_id !== undefined) queryParams.append('location_id', String(params.location_id));
    if (params?.ingredient_code) queryParams.append('ingredient_code', params.ingredient_code);
    
    const response = await apiClient.get<IngredientUsageDaily[]>(`/analytics/inventory/usage-daily?${queryParams.toString()}`);
    return response.data;
  },
};
