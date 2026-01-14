import { useEffect } from 'react';

/**
 * Хук для обработки Telegram Login Widget (OAuth для браузера)
 * Слушает GET параметры от Telegram после авторизации
 */
export function useTelegramOAuth(onAuth: (user: any) => void) {
  useEffect(() => {
    // Проверяем URL параметры после редиректа от Telegram OAuth
    const params = new URLSearchParams(window.location.search);
    const tgId = params.get('id');
    const tgHash = params.get('hash');
    
    if (tgId && tgHash) {
      // Собираем объект пользователя из параметров
      const user: any = { id: parseInt(tgId), hash: tgHash };
      
      // Добавляем остальные параметры если есть
      params.forEach((value, key) => {
        if (key !== 'id' && key !== 'hash') {
          user[key] = isNaN(Number(value)) ? value : Number(value);
        }
      });

      console.log('Telegram OAuth user data:', user);
      onAuth(user);

      // Очищаем URL от параметров
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [onAuth]);
}
