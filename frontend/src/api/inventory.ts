import apiClient from './client';

export interface IngredientLoad {
    id: number;
    ingredient_code: string;
    location_id: number;
    load_date: string;
    qty: number;
    unit: string;
    comment?: string | null;
    created_at: string;
    created_by_user_id?: number | null;
}

export interface IngredientLoadCreate {
    ingredient_code: string;
    location_id: number;
    load_date: string;
    qty: number;
    unit: string;
    comment?: string;
}

export interface InventoryStatusItem {
    ingredient_code: string;
    display_name_ru: string;
    unit: string;
    unit_ru?: string;
    cost_per_unit_rub?: number;
    alert_threshold?: number;
    alert_days_threshold?: number;
    location_id: number;
    location_name: string;
    total_loaded: number;
    total_used: number;
    balance: number;
    is_low_stock: boolean;
}

export const inventoryApi = {
    // Ingredient Loads
    getIngredientLoads: async (params?: {
        ingredient_code?: string;
        location_id?: number;
        from_date?: string;
        to_date?: string;
        skip?: number;
        limit?: number;
    }): Promise<IngredientLoad[]> => {
        const response = await apiClient.get<IngredientLoad[]>('/inventory/ingredient-loads', { params });
        return response.data;
    },

    createIngredientLoad: async (data: IngredientLoadCreate): Promise<IngredientLoad> => {
        const response = await apiClient.post<IngredientLoad>('/inventory/ingredient-loads', data);
        return response.data;
    },

    // Inventory Status (Balance)
    getInventoryStatus: async (params?: {
        location_id?: number;
    }): Promise<InventoryStatusItem[]> => {
        const response = await apiClient.get<InventoryStatusItem[]>('/analytics/inventory/balance', { params });
        return response.data;
    },
};
