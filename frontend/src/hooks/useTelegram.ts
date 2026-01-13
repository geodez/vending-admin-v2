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
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [initData, setInitData] = useState('');
  const [colorScheme, setColorScheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && WebApp) {
        console.log('Initializing Telegram WebApp...');
        
        // Initialize Telegram WebApp
        WebApp.ready();
        WebApp.expand();
        
        // Get user data
        const userData = (WebApp as any)?.initDataUnsafe?.user || null;
        const appInitData = (WebApp as any)?.initData || '';
        const scheme = (WebApp as any)?.colorScheme || 'light';
        
        console.log('Telegram data:', {
          userData,
          appInitData: appInitData?.substring(0, 50) + '...',
          scheme
        });
        
        if (userData) {
          setUser(userData);
        }
        if (appInitData) {
          setInitData(appInitData);
        }
        if (scheme) {
          setColorScheme(scheme);
        }
        
        // Apply theme
        if ((WebApp as any)?.themeParams?.bg_color) {
          document.body.style.backgroundColor = (WebApp as any).themeParams.bg_color;
        }
        
        setIsReady(true);
      } else {
        console.log('WebApp not available, using fallback');
        setIsReady(true);
      }
    } catch (error) {
      console.error('Error initializing Telegram WebApp:', error);
      setIsReady(true);
    }
  }, []);

  const webApp = (WebApp as unknown) as TelegramWebApp;

  return {
    webApp,
    user,
    initData,
    isReady,
    colorScheme,
  };
};
