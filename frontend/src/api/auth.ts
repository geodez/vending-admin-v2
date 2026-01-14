import apiClient from './client';
import { TelegramAuthRequest, TokenResponse, User } from '@/types/api';

export const authApi = {
  /**
   * Authenticate with Telegram initData (POST /auth/telegram_oauth)
   */
  loginWithTelegram: async (initData: string): Promise<TokenResponse> => {
    try {
      console.log('🔐 Sending Telegram initData to backend...');
      const payload: TelegramAuthRequest = { init_data: initData };
      const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
      console.log('📡 API_BASE_URL:', baseUrl);
      // baseURL is already /api/v1, so endpoint is /auth/telegram_oauth
      const response = await apiClient.post<TokenResponse>('/auth/telegram_oauth', payload);
      console.log('✅ Server response received');
      return response.data;
    } catch (error) {
      console.error('❌ Error sending Telegram initData:', error);
      throw error;
    }
  },

  /**
   * Get current user info (GET /auth/me)
   */
  getCurrentUser: async (): Promise<User> => {
    // baseURL is already /api/v1, so endpoint is /auth/me
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};
