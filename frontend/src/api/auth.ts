import apiClient from './client';
import { TelegramAuthRequest, TokenResponse, User, LoginRequest } from '@/types/api';

export const authApi = {
  /**
   * Authenticate with Telegram initData (Mini App)
   */
  loginWithTelegram: async (initData: string): Promise<TokenResponse> => {
    try {
      console.log('🔐 Sending Telegram initData to server...');
      const payload: TelegramAuthRequest = { init_data: initData };
      const response = await apiClient.post<TokenResponse>('/auth/telegram', payload);
      console.log('✅ Response received');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error sending initData:', error);
      throw error;
    }
  },

  /**
   * Authenticate with email and password
   */
  loginWithPassword: async (email: string, password: string): Promise<TokenResponse> => {
    try {
      console.log('🔐 Sending email/password to server...');
      const payload: LoginRequest = { email, password };
      const response = await apiClient.post<TokenResponse>('/auth/login', payload);
      console.log('✅ Login successful');
      return response.data;
    } catch (error: any) {
      console.error('❌ Login error:', error);
      throw error;
    }
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};
