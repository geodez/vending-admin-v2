import apiClient from './client';

export interface Transaction {
  id: number;
  term_id: number;
  vendista_tx_id: number;
  tx_time: string | null;
  sum_rub: number;
  machine_item_id: number | null;
  terminal_comment: string | null;
  status: number | null;
  location_id: number | null;
}

export interface TransactionsResponse {
  items: Transaction[];
  page: number;
  page_size: number;
  total: number;
}

export const transactionsApi = {
  getTransactions: async (params: {
    period_start?: string;
    period_end?: string;
    term_id?: number;
    only_positive?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<TransactionsResponse> => {
    const queryParams = new URLSearchParams();
    if (params.period_start) queryParams.append('period_start', params.period_start);
    if (params.period_end) queryParams.append('period_end', params.period_end);
    if (params.term_id !== undefined) queryParams.append('term_id', String(params.term_id));
    if (params.only_positive !== undefined) queryParams.append('only_positive', String(params.only_positive));
    if (params.page) queryParams.append('page', String(params.page));
    if (params.page_size) queryParams.append('page_size', String(params.page_size));
    
    const response = await apiClient.get<TransactionsResponse>(`/transactions?${queryParams.toString()}`);
    return response.data;
  },
};
