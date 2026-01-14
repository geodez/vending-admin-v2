import { TelegramAuthRequest, TokenResponse } from '@/types/api';
import apiClient from './client';

export const telegramOAuthApi = {
  loginWithTelegramOAuth: async (tgUser: any): Promise<TokenResponse> => {
    // tgUser содержит данные, которые Telegram Login Widget возвращает после авторизации
    // Обычно это id, hash, username, first_name, last_name, photo_url, auth_date
    const payload: TelegramAuthRequest = { init_data: JSON.stringify(tgUser) };
    const response = await apiClient.post<TokenResponse>('/v1/auth/telegram_oauth', payload);
    return response.data;
  },
};
