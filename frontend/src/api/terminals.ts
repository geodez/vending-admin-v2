import apiClient from './client';

export interface Terminal {
  term_id: number;
  tx_count: number;
  revenue_gross: number;
  last_tx_time: string | null;
}

export const terminalsApi = {
  getTerminals: async (periodStart?: string, periodEnd?: string): Promise<Terminal[]> => {
    const params = new URLSearchParams();
    if (periodStart) params.append('period_start', periodStart);
    if (periodEnd) params.append('period_end', periodEnd);
    
    // Добавляем trailing slash чтобы избежать редиректа
    const response = await apiClient.get<Terminal[]>(`/terminals/?${params.toString()}`);
    return response.data;
  },
};
