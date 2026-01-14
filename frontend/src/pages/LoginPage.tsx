import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Typography, Space, Alert } from 'antd';
import { LoginOutlined } from '@ant-design/icons';
import { useTelegram } from '@/hooks/useTelegram';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/api/auth';
import { ROUTES, TELEGRAM_BOT_USERNAME } from '@/utils/constants';

const { Title, Text } = Typography;

const LoginPage = () => {
  const navigate = useNavigate();
  const { initData } = useTelegram();
  const { setUser, setToken, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [oauthLoading, setOauthLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(ROUTES.OVERVIEW);
    }
    
    // Check if token in URL (from Telegram Login Widget redirect)
    const params = new URLSearchParams(window.location.search);
    const tokenFromUrl = params.get('token');
    const userIdFromUrl = params.get('user_id');
    
    if (tokenFromUrl && userIdFromUrl) {
      console.log('Token found in URL, authenticating...');
      setToken(tokenFromUrl);
      localStorage.removeItem('telegram_auth_pending');
      
      authApi.getCurrentUser().then((userData) => {
        setUser(userData);
        window.history.replaceState({}, document.title, window.location.pathname);
        navigate(ROUTES.OVERVIEW);
      }).catch((err) => {
        console.error('Error loading user data:', err);
        setError('Failed to load user data');
      });
    }
  }, [isAuthenticated, navigate, setToken, setUser]);

  const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';
  const isDev = !import.meta.env.PROD;
  const hasDebugParam = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').has('debug');
  const isDebugMode = (isLocalhost && isDev) || hasDebugParam;
  const isInTelegram = !!initData;
  const buttonDisabled = !initData && !isDebugMode;
  
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    typeof window !== 'undefined' ? navigator.userAgent : ''
  );

  // Mini App Login Handler
  const handleLogin = async () => {
    if (!initData) {
      setError('Telegram data unavailable. Open app via Telegram.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('🔐 Sending Telegram initData...');
      const response = await authApi.loginWithTelegram(initData);
      console.log('✅ Login successful!', response);
      setToken(response.access_token);
      setUser(response.user);
      navigate(ROUTES.OVERVIEW);
    } catch (err: any) {
      console.error('❌ Login error:', err);
      setError(
        err.response?.data?.detail || 
        `Login failed: ${err.message || 'Check console'}`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleMobileTelegramAuth = () => {
    const authId = `webauth_${Date.now()}`;
    localStorage.setItem('telegram_auth_pending', authId);
    const telegramLink = `https://t.me/${TELEGRAM_BOT_USERNAME}/vendingadmin?startapp=${authId}`;
    console.log('Opening Telegram:', telegramLink);
    window.location.href = telegramLink;
  };

  // Telegram Login Widget for desktop
  useEffect(() => {
    if (isInTelegram || isMobile) return;
    
    // Global callback for Telegram Widget
    (window as any).onTelegramAuth = async (user: any) => {
      console.log('Telegram auth callback received:', user);
      setOauthLoading(true);
      setError(null);
      
      try {
        // Send user data to backend
        const payload = { init_data: JSON.stringify(user) };
        const response = await authApi.loginWithTelegram(JSON.stringify(payload));
        setToken(response.access_token);
        setUser(response.user);
        navigate(ROUTES.OVERVIEW);
      } catch (err: any) {
        console.error('Login error:', err);
        setError(
          err.response?.data?.detail || 
          `Login failed: ${err.message || 'Check console'}`
        );
      } finally {
        setOauthLoading(false);
      }
    };
    
    // Setup Telegram Login Widget
    const widgetContainer = document.getElementById('telegram-login-widget');
    if (!widgetContainer) return;
    
    widgetContainer.innerHTML = '';
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', TELEGRAM_BOT_USERNAME.replace('@', ''));
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-radius', '8');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.async = true;
    
    widgetContainer.appendChild(script);
    console.log('Telegram Login Widget initialized');
  }, [isInTelegram, isMobile, navigate, setToken, setUser]);

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
              Vending Business Management System
            </Text>
          </div>

          {error && (
            <Alert
              message="Login Error"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
            />
          )}

          {/* Telegram OAuth for browser */}
          {!isInTelegram && (
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
                Login via Telegram to access admin panel
              </Text>
              
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
                  🔐 Open in Telegram
                </Button>
              ) : (
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
                  Authenticating via Telegram...
                </Text>
              )}
            </div>
          )}

          {/* Login button for Mini App */}
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
              {loading ? 'Logging in...' : 'Login via Telegram'}
            </Button>
          )}

          {!isInTelegram && !isDebugMode && (
            <Alert
              message="Telegram Login"
              description={
                isMobile 
                  ? "Tap the button above to open Telegram app. After confirmation you will return to browser authenticated."
                  : "Click the button above to authenticate. After Telegram confirmation you will continue in browser."
              }
              type="info"
              showIcon
            />
          )}
          
          {!isInTelegram && isDebugMode && (
            <Alert
              message="DEBUG MODE: Test data loaded"
              description="You can use test Telegram data for debugging"
              type="success"
              showIcon
            />
          )}

          <div style={{ textAlign: 'center', marginTop: 24 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Version 1.0.0 • © 2026 Vending Admin
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;
