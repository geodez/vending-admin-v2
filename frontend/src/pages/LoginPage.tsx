import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Typography, Space, Alert, Form, Input, Tabs } from 'antd';
import { LoginOutlined, MailOutlined, LockOutlined } from '@ant-design/icons';
import { useTelegram } from '@/hooks/useTelegram';
import { useAuthStore } from '@/store/authStore';
import { APP_VERSION } from '@/utils/constants';
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
  const [activeTab, setActiveTab] = useState<string>('telegram');
  const [form] = Form.useForm();

  useEffect(() => {
    if (isAuthenticated) {
      navigate(ROUTES.OVERVIEW);
    }

    // Проверяем, есть ли токен в URL (после Telegram Login Widget или возврата из Web App)
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get('token');
    const userIdFromUrl = params.get('user_id');

    if (tokenFromUrl && userIdFromUrl) {
      console.log('Найден токен в URL, выполняем авторизацию...');
      setToken(tokenFromUrl);

      // Очищаем localStorage от pending статуса
      localStorage.removeItem('telegram_auth_pending');

      // Получаем данные пользователя
      authApi.getCurrentUser().then((userData) => {
        setUser(userData);
        // Очищаем URL от параметров
        window.history.replaceState({}, document.title, window.location.pathname);
        navigate(ROUTES.OVERVIEW);
      }).catch((err) => {
        console.error('Ошибка получения данных пользователя:', err);
        setError('Не удалось загрузить данные пользователя');
      });
    }
  }, [isAuthenticated, navigate, setToken, setUser]);

  const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';
  const isDev = !import.meta.env.PROD;
  const hasDebugParam = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').has('debug');
  const isDebugMode = (isLocalhost && isDev) || hasDebugParam;
  const isInTelegram = !!initData; // Если initData есть - мы в Telegram
  const buttonDisabled = !initData && !isDebugMode;

  // Определяем тип устройства
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    typeof window !== 'undefined' ? navigator.userAgent : ''
  );

  // Обработка Telegram OAuth авторизации (браузер)
  useTelegramOAuth(async (tgUser) => {
    setOauthLoading(true);
    setError(null);
    try {
      console.log('🔐 Processing Telegram OAuth callback...');
      const response = await telegramOAuthApi.loginWithTelegramOAuth(tgUser);
      console.log('✅ OAuth successful, storing token...');
      setToken(response.access_token);
      setUser(response.user);
      navigate(ROUTES.OVERVIEW);
    } catch (err: any) {
      console.error('❌ OAuth error:', err.response?.status, err.response?.data);

      // Обработка 403 - доступ запрещен
      if (err.response?.status === 403) {
        setError('Доступ запрещен. Ваш аккаунт не имеет доступа к этой системе.');
      } else if (err.response?.status === 401) {
        setError('Ошибка авторизации. Попробуйте ещё раз.');
      } else {
        setError(
          err.response?.data?.detail ||
          `Ошибка входа: ${err.message || 'Проверьте консоль'}`
        );
      }
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

  const handlePasswordLogin = async (values: { email: string; password: string }) => {
    setLoading(true);
    setError(null);

    try {
      console.log('📧 Отправляем запрос на авторизацию по email...');
      const response = await authApi.loginWithPassword(values.email, values.password);
      console.log('✅ Авторизация успешна!', response);
      setToken(response.access_token);
      setUser(response.user);
      navigate(ROUTES.OVERVIEW);
    } catch (err: any) {
      console.error('❌ Login error:', err);
      setError(
        err.response?.data?.detail ||
        `Ошибка входа: ${err.message || 'Неверный email или пароль'}`
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

  // Обработчик для мобильных устройств - открывает Telegram приложение
  const handleMobileTelegramAuth = () => {
    // Генерируем уникальный ID для этой сессии авторизации
    const authId = `webauth_${Date.now()}`;

    // Сохраняем в localStorage, чтобы знать что ожидаем возврата
    localStorage.setItem('telegram_auth_pending', authId);

    // Открываем Web App в Telegram через deep link
    // При открытии Web App получит initData и сможет авторизоваться
    const telegramLink = `https://t.me/coffeekznebot/vendingadmin?startapp=${authId}`;

    console.log('Открываем Telegram приложение:', telegramLink);
    window.location.href = telegramLink;
  };

  // Инициализируем Telegram Login Widget для десктопа
  useEffect(() => {
    if (isInTelegram || isMobile || activeTab !== 'telegram') return; // На мобильных и в Telegram не показываем виджет

    // Создаем глобальную функцию для callback от Telegram Widget
    (window as any).onTelegramAuth = async (user: any) => {
      console.log('Telegram auth callback received:', user);
      setOauthLoading(true);
      setError(null);

      try {
        // Отправляем данные на backend через POST
        const response = await telegramOAuthApi.loginWithTelegramOAuth(user);
        setToken(response.access_token);
        setUser(response.user);
        navigate(ROUTES.OVERVIEW);
      } catch (err: any) {
        console.error('Login error:', err);
        setError(
          err.response?.data?.detail ||
          `Ошибка входа: ${err.message || 'Проверьте консоль'}`
        );
      } finally {
        setOauthLoading(false);
      }
    };

    // Создаем контейнер для виджета если его еще нет
    const widgetContainer = document.getElementById('telegram-login-widget');
    if (!widgetContainer) return;

    // Очищаем предыдущий виджет
    widgetContainer.innerHTML = '';

    // Создаем скрипт для Telegram Login Widget
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', 'coffeekznebot');
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '8');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;

    widgetContainer.appendChild(script);

    console.log('Telegram Login Widget инициализирован с callback');
  }, [isInTelegram, isMobile, navigate, setToken, setUser, activeTab]);

  const tabItems = [
    {
      key: 'telegram',
      label: '🔐 Telegram',
      children: (
        <div>
          {error && (
            <Alert
              message="Ошибка входа"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 16 }}
            />
          )}

          {user && (
            <Alert
              message={`Привет, ${user.first_name || 'пользователь'}!`}
              description="Нажмите кнопку ниже для входа в систему"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* Telegram OAuth для браузера */}
          {!isInTelegram && (
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                Войдите через Telegram для доступа к админ-панели
              </Text>

              {/* Для мобильных - кнопка открытия Telegram приложения */}
              {isMobile ? (
                <Button
                  type="primary"
                  size="large"
                  icon={<LoginOutlined />}
                  block
                  onClick={handleMobileTelegramAuth}
                  loading={oauthLoading}
                  style={{ marginBottom: 16 }}
                >
                  🔐 Открыть в Telegram
                </Button>
              ) : (
                /* Для десктопа - Telegram Login Widget */
                <div
                  id="telegram-login-widget"
                  style={{
                    display: 'flex',
                    justifyContent: 'center',
                    marginBottom: 16
                  }}
                />
              )}

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
              description={
                isMobile
                  ? "Нажмите кнопку выше для открытия Telegram приложения. После подтверждения вы вернетесь в браузер авторизованным."
                  : "Нажмите кнопку выше для авторизации. После подтверждения в Telegram вы продолжите работу в браузере."
              }
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          )}
        </div>
      ),
    },
    {
      key: 'password',
      label: '📧 Email',
      children: (
        <div>
          {error && (
            <Alert
              message="Ошибка входа"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
              style={{ marginBottom: 16 }}
            />
          )}

          <Form
            form={form}
            name="login"
            onFinish={handlePasswordLogin}
            autoComplete="off"
            layout="vertical"
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Введите email' },
                { type: 'email', message: 'Введите корректный email' },
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="Email"
                size="large"
                autoComplete="email"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Введите пароль' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Пароль"
                size="large"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                loading={loading}
                icon={<LoginOutlined />}
              >
                {loading ? 'Вход...' : 'Войти'}
              </Button>
            </Form.Item>
          </Form>

          <Alert
            message="Вход по email и паролю"
            description="Используйте учетные данные, предоставленные администратором системы."
            type="info"
            showIcon
          />
        </div>
      ),
    },
  ];

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
          maxWidth: 450,
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

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            centered
          />

          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Версия {APP_VERSION} • © 2026 Vending Admin
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;
