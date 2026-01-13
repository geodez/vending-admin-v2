import apiClient from './client';
import { TelegramAuthRequest, TokenResponse, User } from '@/types/api';

export const authApi = {
  /**
   * Authenticate with Telegram initData
   */
  loginWithTelegram: async (initData: string): Promise<TokenResponse> => {
    try {
      console.log('🔐 Отправляем Telegram initData на сервер...');
      const payload: TelegramAuthRequest = { init_data: initData };
      console.log('📡 API_BASE_URL:', import.meta.env.VITE_API_BASE_URL || 'http://155.212.160.190:8000');
      const response = await apiClient.post<TokenResponse>('/v1/auth/telegram', payload);
      console.log('✅ Ответ от сервера получен');
      return response.data;
    } catch (error) {
      console.error('❌ Ошибка при отправке initData:', error);
      throw error;
    }
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },
};
