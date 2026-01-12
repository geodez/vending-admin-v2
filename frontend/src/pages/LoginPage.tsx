import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Typography, Space, Alert, Spin } from 'antd';
import { LoginOutlined } from '@ant-design/icons';
import { useTelegram } from '@/hooks/useTelegram';
import { useAuthStore } from '@/store/authStore';
import { authApi } from '@/api/auth';
import { ROUTES } from '@/utils/constants';

const { Title, Text } = Typography;

const LoginPage = () => {
  const navigate = useNavigate();
  const { initData, user } = useTelegram();
  const { setUser, setToken, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      navigate(ROUTES.OVERVIEW);
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async () => {
    if (!initData) {
      setError('Telegram данные недоступны. Откройте приложение через Telegram.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await authApi.loginWithTelegram(initData);
      setToken(response.access_token);
      setUser(response.user);
      navigate(ROUTES.OVERVIEW);
    } catch (err: any) {
      console.error('Login error:', err);
      setError(
        err.response?.data?.detail || 
        'Ошибка входа. Возможно, у вас нет доступа к системе.'
      );
    } finally {
      setLoading(false);
    }
  };

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

          <Button
            type="primary"
            size="large"
            icon={<LoginOutlined />}
            block
            loading={loading}
            onClick={handleLogin}
            disabled={!initData}
          >
            {loading ? 'Вход...' : 'Войти через Telegram'}
          </Button>

          {!initData && (
            <Alert
              message="Откройте через Telegram"
              description="Это приложение работает только через Telegram Mini App"
              type="warning"
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
