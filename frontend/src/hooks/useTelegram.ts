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
        console.log('🚀 Инициализация Telegram WebApp...');
        
        // Initialize Telegram WebApp
        WebApp.ready();
        WebApp.expand();
        
        // Get user data
        const userData = (WebApp as any)?.initDataUnsafe?.user || null;
        const appInitData = (WebApp as any)?.initData || '';
        const scheme = (WebApp as any)?.colorScheme || 'light';
        
        console.log('📊 Данные Telegram:', {
          userData,
          appInitData: appInitData?.substring(0, 50) + '...',
          scheme
        });
        
        if (userData) {
          console.log('👤 Пользователь найден:', userData.id, userData.first_name);
          setUser(userData);
        } else {
          console.warn('⚠️ Пользователь не найден в initDataUnsafe');
        }
        if (appInitData) {
          console.log('🔐 initData получен (длина: ' + appInitData.length + ')');
          setInitData(appInitData);
        } else {
          console.warn('⚠️ initData пуст');
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
        console.warn('⚠️ WebApp недоступен, возможно приложение не открыто через Telegram');
        
        // DEV MODE: Если открыто не через Telegram, используем test данные
        const isDev = !import.meta.env.PROD;
        if (isDev && window.location.hostname === 'localhost') {
          console.log('💻 DEV MODE: Используем test Telegram данные');
          
          // Test user data
          const testUser: TelegramUser = {
            id: 602720033,
            is_bot: false,
            first_name: 'Roman',
            last_name: 'Test',
            username: 'roman_test',
            language_code: 'ru',
            is_premium: false,
            allows_write_to_pm: true,
          };
          
          // Генерируем test initData
          const testInitData = `query_id=test&user=${JSON.stringify(testUser)}&auth_date=${Math.floor(Date.now() / 1000)}&hash=test`;
          
          console.log('📱 Test initData:', testInitData);
          setUser(testUser);
          setInitData(testInitData);
        }
        
        setIsReady(true);
      }
    } catch (error) {
      console.error('❌ Ошибка инициализации Telegram WebApp:', error);
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
