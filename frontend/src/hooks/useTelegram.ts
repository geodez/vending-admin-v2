import { useEffect, useState } from 'react';
import WebApp from '@twa-dev/sdk';
import { TelegramWebApp, TelegramUser } from '@/types/telegram';

interface UseTelegramReturn {
  webApp: TelegramWebApp | null;
  user: TelegramUser | null;
  initData: string;
  isReady: boolean;
  colorScheme: 'light' | 'dark';
}

/**
 * Hook for Telegram WebApp integration
 */
export const useTelegram = (): UseTelegramReturn => {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && WebApp) {
      // Initialize Telegram WebApp
      WebApp.ready();
      WebApp.expand();
      
      // Apply theme
      if (WebApp.themeParams.bg_color) {
        document.body.style.backgroundColor = WebApp.themeParams.bg_color;
      }
      
      setIsReady(true);
    }
  }, []);

  const webApp = (WebApp as unknown) as TelegramWebApp;
  const user = webApp?.initDataUnsafe?.user || null;
  const initData = webApp?.initData || '';
  const colorScheme = webApp?.colorScheme || 'light';

  return {
    webApp,
    user,
    initData,
    isReady,
    colorScheme,
  };
};
