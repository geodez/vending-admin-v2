import apiClient from './client';

export interface Expense {
  id: number;
  expense_date: string;
  location_id: number;
  category: string;
  amount_rub: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  expense_date: string;
  location_id: number;
  category: string;
  amount_rub: number;
  comment?: string;
}

export interface ExpenseUpdate {
  expense_date?: string;
  location_id?: number;
  category?: string;
  amount_rub?: number;
  comment?: string;
}

export const expensesApi = {
  getExpenses: async (params?: {
    period_start?: string;
    period_end?: string;
    location_id?: number;
    category?: string;
  }): Promise<Expense[]> => {
    const queryParams = new URLSearchParams();
    if (params?.period_start) queryParams.append('period_start', params.period_start);
    if (params?.period_end) queryParams.append('period_end', params.period_end);
    if (params?.location_id !== undefined) queryParams.append('location_id', String(params.location_id));
    if (params?.category) queryParams.append('category', params.category);
    
    const response = await apiClient.get<Expense[]>(`/expenses?${queryParams.toString()}`);
    return response.data;
  },

  createExpense: async (data: ExpenseCreate): Promise<Expense> => {
    const response = await apiClient.post<Expense>('/expenses', data);
    return response.data;
  },

  updateExpense: async (id: number, data: ExpenseUpdate): Promise<Expense> => {
    const response = await apiClient.patch<Expense>(`/expenses/${id}`, data);
    return response.data;
  },

  deleteExpense: async (id: number): Promise<void> => {
    await apiClient.delete(`/expenses/${id}`);
  },
};
