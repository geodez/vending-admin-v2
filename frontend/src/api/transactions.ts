import apiClient from './client';

export interface Transaction {
  id: number;
  term_id: number;
  vendista_tx_id: number;
  tx_time: string | null;
  sum_rub: number;
  sum_kopecks: number;
  machine_item_id: number | null;
  terminal_comment: string | null;
  status: number | null;
  location_id: number | null;
  drink_name: string | null;  // Название напитка из machine_matrix
}

export interface TransactionsResponse {
  items: Transaction[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export const transactionsApi = {
  getTransactions: async (params: {
    date_from?: string;
    date_to?: string;
    term_id?: number;
    sum_type?: 'all' | 'positive' | 'non_positive';
    page?: number;
    page_size?: number;
  }): Promise<TransactionsResponse> => {
    const queryParams = new URLSearchParams();
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    if (params.term_id !== undefined) queryParams.append('term_id', String(params.term_id));
    if (params.sum_type) queryParams.append('sum_type', params.sum_type);
    if (params.page) queryParams.append('page', String(params.page));
    if (params.page_size) queryParams.append('page_size', String(params.page_size));
    
    // Добавляем trailing slash чтобы избежать редиректа
    const response = await apiClient.get<TransactionsResponse>(`/transactions/?${queryParams.toString()}`);
    return response.data;
  },

  exportTransactions: async (params: {
    date_from?: string;
    date_to?: string;
    term_id?: number;
    sum_type?: 'all' | 'positive' | 'non_positive';
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams();
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    if (params.term_id !== undefined) queryParams.append('term_id', String(params.term_id));
    if (params.sum_type) queryParams.append('sum_type', params.sum_type);
    
    // Добавляем trailing slash для консистентности
    const response = await apiClient.get(`/transactions/export?${queryParams.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
