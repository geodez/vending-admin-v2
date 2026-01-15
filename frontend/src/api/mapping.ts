import apiClient from './client';

export interface Drink {
  id: number;
  name: string;
  purchase_price_rub: number | null;
  sale_price_rub: number | null;
  is_active: boolean;
}

export interface DrinkCreate {
  name: string;
  purchase_price_rub?: number;
  sale_price_rub?: number;
  is_active?: boolean;
}

export interface MachineMatrix {
  id: number;
  term_id: number;
  machine_item_id: number;
  drink_id: number;
  location_id: number;
  is_active: boolean;
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

  // Machine Matrix
  getMachineMatrix: async (termId?: number): Promise<MachineMatrix[]> => {
    const params = termId !== undefined ? `?term_id=${termId}` : '';
    const response = await apiClient.get<MachineMatrix[]>(`/mapping/machine-matrix${params}`);
    return response.data;
  },

  bulkCreateMachineMatrix: async (items: MachineMatrixCreate[]): Promise<{ inserted: number; message: string }> => {
    const response = await apiClient.post<{ inserted: number; message: string }>('/mapping/machine-matrix/bulk', items);
    return response.data;
  },

  deleteMachineMatrix: async (id: number): Promise<void> => {
    await apiClient.delete(`/mapping/machine-matrix/${id}`);
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
};
