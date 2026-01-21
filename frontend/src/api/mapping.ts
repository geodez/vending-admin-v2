import apiClient from './client';

export interface DrinkItem {
  ingredient_code: string;
  qty_per_unit: number;
  unit: string;
  display_name_ru?: string;
  cost_per_unit_rub?: number;
  item_cost_rub?: number;  // Стоимость этого ингредиента в рецепте
}

export interface Drink {
  id: number;
  name: string;
  is_active: boolean;
  created_at?: string;
  items?: DrinkItem[];
  cogs_rub?: number;  // Себестоимость напитка (COGS)
}

export interface DrinkCreate {
  name: string;
  is_active?: boolean;
  items?: DrinkItem[];
}

export interface DrinkUpdate {
  name?: string;
  is_active?: boolean;
  items?: DrinkItem[];
}

export interface MachineMatrix {
  term_id: number;
  machine_item_id: number;
  drink_id: number | null;
  location_id: number | null;
  is_active: boolean;
  term_name?: string | null;  // Название терминала
  drink_name?: string | null;  // Название напитка
  location_name?: string | null;  // Название локации
}

export interface MachineMatrixCreate {
  term_id: number;
  machine_item_id: number;
  drink_id: number;
  location_id: number;
  is_active?: boolean;
}

export interface ImportPreviewRow {
  term_id: number;
  machine_item_id: number;
  drink_id: number;
  location_id: number;
  is_active: boolean;
}

export interface ImportPreviewResponse {
  total_rows: number;
  valid_rows: number;
  errors: Array<{ row: number; error: string }>;
  preview: ImportPreviewRow[];
}

export interface ImportApplyResponse {
  inserted: number;
  updated: number;
  errors: Array<{ term_id?: number; machine_item_id?: number; error: string }>;
  message: string;
}

// Button Matrix (Template System)
export interface ButtonMatrix {
  id: number;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ButtonMatrixCreate {
  name: string;
  description?: string | null;
  is_active?: boolean;
}

export interface ButtonMatrixUpdate {
  name?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface ButtonMatrixItem {
  machine_item_id: number;
  drink_id: number | null;
  sale_price_rub?: number | null;
  is_active: boolean;
  drink_name?: string | null;
  cogs_rub?: number | null;  // Себестоимость напитка из рецепта
}

export interface ButtonMatrixItemCreate {
  machine_item_id: number;
  drink_id?: number | null;
  sale_price_rub?: number | null;
  is_active?: boolean;
}

export interface ButtonMatrixItemUpdate {
  drink_id?: number | null;
  sale_price_rub?: number | null;
  is_active?: boolean;
}

export interface ButtonMatrixWithItems extends ButtonMatrix {
  items: ButtonMatrixItem[];
}

export interface TerminalMatrixMap {
  matrix_id: number;
  matrix_name: string;
  vendista_term_id: number;
  term_name?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TerminalMatrixMapCreate {
  vendista_term_ids: number[];
}

export const mappingApi = {
  // Drinks
  getDrinks: async (): Promise<Drink[]> => {
    const response = await apiClient.get<Drink[]>('/mapping/drinks');
    return response.data;
  },

  createDrink: async (data: DrinkCreate): Promise<Drink> => {
    const response = await apiClient.post<Drink>('/mapping/drinks', data);
    return response.data;
  },

  updateDrink: async (drinkId: number, data: DrinkUpdate): Promise<Drink> => {
    const response = await apiClient.put<Drink>(`/mapping/drinks/${drinkId}`, data);
    return response.data;
  },

  deleteDrink: async (drinkId: number): Promise<void> => {
    await apiClient.delete(`/mapping/drinks/${drinkId}`);
  },

  bulkUpdateDrinks: async (drinkIds: number[], data: { is_active?: boolean }): Promise<{ updated: number; total: number }> => {
    const response = await apiClient.put<{ updated: number; total: number }>('/mapping/drinks/bulk/update', {
      drink_ids: drinkIds,
      ...data
    });
    return response.data;
  },

  // Machine Matrix
  getMachineMatrix: async (termId?: number): Promise<MachineMatrix[]> => {
    const params = termId !== undefined ? `?term_id=${termId}` : '';
    const response = await apiClient.get<MachineMatrix[]>(`/mapping/machine-matrix${params}`);
    return response.data;
  },

  createMachineMatrix: async (data: MachineMatrixCreate): Promise<MachineMatrix> => {
    const response = await apiClient.post<MachineMatrix>('/mapping/machine-matrix', data);
    return response.data;
  },

  bulkCreateMachineMatrix: async (items: MachineMatrixCreate[]): Promise<{ inserted: number; message: string }> => {
    const response = await apiClient.post<{ inserted: number; message: string }>('/mapping/machine-matrix/bulk', items);
    return response.data;
  },

  deleteMachineMatrix: async (termId: number, machineItemId: number): Promise<void> => {
    await apiClient.delete(`/mapping/machine-matrix?term_id=${termId}&machine_item_id=${machineItemId}`);
  },

  // CSV Import
  dryRunImport: async (file: File): Promise<ImportPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<ImportPreviewResponse>(
      '/mapping/matrix/import?dry_run=true',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  applyImport: async (file: File): Promise<ImportApplyResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<ImportApplyResponse>(
      '/mapping/matrix/import?dry_run=false',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  },

  // Button Matrices (Templates)
  getButtonMatrices: async (isActive?: boolean, skip?: number, limit?: number): Promise<ButtonMatrix[]> => {
    const params = new URLSearchParams();
    if (isActive !== undefined) params.append('is_active', String(isActive));
    if (skip !== undefined) params.append('skip', String(skip));
    if (limit !== undefined) params.append('limit', String(limit));
    const query = params.toString();
    const response = await apiClient.get<ButtonMatrix[]>(`/mapping/button-matrices${query ? `?${query}` : ''}`);
    return response.data;
  },

  getButtonMatrix: async (matrixId: number): Promise<ButtonMatrixWithItems> => {
    const response = await apiClient.get<ButtonMatrixWithItems>(`/mapping/button-matrices/${matrixId}`);
    return response.data;
  },

  createButtonMatrix: async (data: ButtonMatrixCreate): Promise<ButtonMatrix> => {
    const response = await apiClient.post<ButtonMatrix>('/mapping/button-matrices', data);
    return response.data;
  },

  updateButtonMatrix: async (matrixId: number, data: ButtonMatrixUpdate): Promise<ButtonMatrix> => {
    const response = await apiClient.put<ButtonMatrix>(`/mapping/button-matrices/${matrixId}`, data);
    return response.data;
  },

  deleteButtonMatrix: async (matrixId: number): Promise<void> => {
    await apiClient.delete(`/mapping/button-matrices/${matrixId}`);
  },

  // Button Matrix Items
  createButtonMatrixItem: async (matrixId: number, data: ButtonMatrixItemCreate): Promise<ButtonMatrixItem> => {
    const response = await apiClient.post<ButtonMatrixItem>(`/mapping/button-matrices/${matrixId}/items`, data);
    return response.data;
  },

  updateButtonMatrixItem: async (matrixId: number, machineItemId: number, data: ButtonMatrixItemUpdate): Promise<ButtonMatrixItem> => {
    const response = await apiClient.put<ButtonMatrixItem>(`/mapping/button-matrices/${matrixId}/items/${machineItemId}`, data);
    return response.data;
  },

  deleteButtonMatrixItem: async (matrixId: number, machineItemId: number): Promise<void> => {
    await apiClient.delete(`/mapping/button-matrices/${matrixId}/items/${machineItemId}`);
  },

  // Terminal Matrix Mapping
  assignTerminalsToMatrix: async (matrixId: number, data: TerminalMatrixMapCreate): Promise<TerminalMatrixMap[]> => {
    const response = await apiClient.post<TerminalMatrixMap[]>(`/mapping/button-matrices/${matrixId}/assign-terminals`, data);
    return response.data;
  },

  getMatrixTerminals: async (matrixId: number): Promise<TerminalMatrixMap[]> => {
    const response = await apiClient.get<TerminalMatrixMap[]>(`/mapping/button-matrices/${matrixId}/terminals`);
    return response.data;
  },

  removeTerminalFromMatrix: async (matrixId: number, termId: number): Promise<void> => {
    await apiClient.delete(`/mapping/button-matrices/${matrixId}/terminals/${termId}`);
  },
};
