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
      
      // DEBUG: Проверяем auth_date (должен быть текущим)
      const now = Math.floor(Date.now() / 1000);
      const authAge = now - (tgUser.auth_date || 0);
      
      console.log('🔐 Telegram Login Widget callback received:', {
        id: tgUser.id,
        first_name: tgUser.first_name,
        auth_date: tgUser.auth_date,
        auth_age_seconds: authAge,
        auth_date_iso: new Date((tgUser.auth_date || 0) * 1000).toISOString(),
        hash_prefix: tgUser.hash?.substring(0, 6),
        keys: Object.keys(tgUser).sort(),
      });
      
      if (authAge > 86400) {
        console.warn('⚠️ auth_date is older than 24h!', { authAge });
      }
      
      // Отправляем данные напрямую без обёртки (плоский объект)
      const response = await apiClient.post<TokenResponse>(
        '/auth/telegram_oauth', 
        tgUser  // Отправляем объект напрямую, а не { init_data: JSON.stringify(...) }
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
