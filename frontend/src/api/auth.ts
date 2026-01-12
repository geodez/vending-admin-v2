import apiClient from './client';
import { TelegramAuthRequest, TokenResponse, User } from '@/types/api';

export const authApi = {
  /**
   * Authenticate with Telegram initData
   */
  loginWithTelegram: async (initData: string): Promise<TokenResponse> => {
    const payload: TelegramAuthRequest = { init_data: initData };
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/telegram', payload);
    return response.data;
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },
};
