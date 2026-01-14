import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Typography, Space, Alert } from 'antd';
import { LoginOutlined } from '@ant-design/icons';
import { useTelegram } from '@/hooks/useTelegram';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/api/auth';
import { ROUTES, TELEGRAM_BOT_USERNAME } from '@/utils/constants';
import { useTelegramOAuth } from '@/hooks/useTelegramOAuth';
import { telegramOAuthApi } from '@/api/telegramOAuth';

const { Title, Text } = Typography;

const LoginPage = () => {
  const navigate = useNavigate();
  const { initData, user } = useTelegram();
  const { setUser, setToken, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [oauthLoading, setOauthLoading] = useState(false);
  const widgetRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate(ROUTES.OVERVIEW);
    }
  }, [isAuthenticated, navigate]);

  const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';
  const isDev = !import.meta.env.PROD;
  const hasDebugParam = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').has('debug');
  const isDebugMode = (isLocalhost && isDev) || hasDebugParam;
  const isInTelegram = !!initData; // Если initData есть - мы в Telegram
  const buttonDisabled = !initData && !isDebugMode;

  // Обработка Telegram OAuth авторизации (браузер)
  useTelegramOAuth(async (tgUser) => {
    setOauthLoading(true);
    setError(null);
    try {
      const response = await telegramOAuthApi.loginWithTelegramOAuth(tgUser);
      setToken(response.access_token);
      setUser(response.user);
      navigate(ROUTES.OVERVIEW);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        `Ошибка входа через Telegram OAuth: ${err.message || 'Проверьте консоль'}`
      );
    } finally {
      setOauthLoading(false);
    }
  });

  const handleLogin = async () => {
    if (!initData) {
      setError('Telegram данные недоступны. Откройте приложение через Telegram.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('📱 Отправляем запрос на авторизацию...');
      console.log('initData длина:', initData.length);
      const response = await authApi.loginWithTelegram(initData);
      console.log('✅ Авторизация успешна!', response);
      setToken(response.access_token);
      setUser(response.user);
      navigate(ROUTES.OVERVIEW);
    } catch (err: any) {
      console.error('❌ Login error:', err);
      console.error('Status:', err.response?.status);
      console.error('Data:', err.response?.data);
      console.error('Message:', err.message);
      setError(
        err.response?.data?.detail || 
        `Ошибка входа: ${err.message || 'Проверьте консоль'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleOpenTelegram = () => {
    // Открываем Telegram бота с параметром startapp (универсальный deep link)
    const telegramUrl = `https://t.me/${TELEGRAM_BOT_USERNAME}?startapp=login_${Date.now()}`;
    console.log('🔗 Открываем Telegram:', telegramUrl);
    window.location.href = telegramUrl;
  };

  // Инициализируем Telegram Login Widget для браузера
  useEffect(() => {
    if (isInTelegram) return;
    const container = widgetRef.current;
    if (!container) return;

    // Очищаем и вставляем скрипт в контейнер
    container.innerHTML = '';

    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.async = true;
    script.setAttribute('data-telegram-login', TELEGRAM_BOT_USERNAME);
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-userpic', 'false');
    script.setAttribute('data-auth-url', window.location.origin);
    script.setAttribute('data-request-access', 'write');

    container.appendChild(script);

    return () => {
      if (container) container.innerHTML = '';
    };
  }, [isInTelegram]);

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 16,
      }}
    >
      <Card
        style={{
          maxWidth: 400,
          width: '100%',
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>☕</div>
            <Title level={2} style={{ marginBottom: 8 }}>
              Vending Admin
            </Title>
            <Text type="secondary">
              Система управления вендинговым бизнесом
            </Text>
          </div>

          {error && (
            <Alert
              message="Ошибка входа"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
            />
          )}

          {user && (
            <Alert
              message={`Привет, ${user.first_name || 'пользователь'}!`}
              description="Нажмите кнопку ниже для входа в систему"
              type="info"
              showIcon
            />
          )}

          {/* Telegram OAuth для браузера */}
          {!isInTelegram && (
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                Войдите через Telegram для доступа к админ-панели
              </Text>
              <div ref={widgetRef} />
              {oauthLoading && (
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  Авторизация через Telegram...
                </Text>
              )}
            </div>
          )}

          {/* Кнопка для входа внутри Telegram Mini App */}
          {isInTelegram && (
            <Button
              type="primary"
              size="large"
              icon={<LoginOutlined />}
              block
              loading={loading}
              onClick={handleLogin}
              disabled={buttonDisabled}
            >
              {loading ? 'Вход...' : 'Войти через Telegram'}
            </Button>
          )}

          {!isInTelegram && !isDebugMode && (
            <Alert
              message="Вход через Telegram"
              description="Нажмите кнопку выше для авторизации. После подтверждения в Telegram вы продолжите работу в браузере."
              type="info"
              showIcon
            />
          )}
          
          {!isInTelegram && isDebugMode && (
            <Alert
              message="DEBUG MODE: Test данные загружены"
              description="Вы можете использовать test Telegram данные для отладки"
              type="success"
              showIcon
            />
          )}

          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Версия 1.0.0 • © 2026 Vending Admin
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;
