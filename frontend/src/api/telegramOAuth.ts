import { TelegramAuthRequest, TokenResponse } from '@/types/api';
import apiClient from './client';

export const telegramOAuthApi = {
  /**
   * Authenticate via Telegram Login Widget
   * Sends user data from Telegram OAuth callback to backend
   */
  loginWithTelegramOAuth: async (tgUser: any): Promise<TokenResponse> => {
    try {
      // tgUser содержит данные от Telegram Login Widget:
      // { id, hash, username, first_name, last_name, auth_date, photo_url }
      const payload: TelegramAuthRequest = { 
        init_data: JSON.stringify(tgUser) 
      };
      
      console.log('📤 Sending OAuth request to /auth/telegram_oauth', {
        id: tgUser.id,
        auth_date: tgUser.auth_date,
      });
      
      const response = await apiClient.post<TokenResponse>(
        '/auth/telegram_oauth', 
        payload
      );
      
      console.log('✅ OAuth login successful');
      return response.data;
    } catch (error: any) {
      console.error('❌ OAuth login failed:', {
        status: error.response?.status,
        detail: error.response?.data?.detail,
        message: error.message,
      });
      throw error;
    }
  },
};
