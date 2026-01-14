import { useEffect, useState } from 'react';
import { Card, Typography, Empty, Alert, Button, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { ROUTES, ROLES } from '@/utils/constants';

const { Title, Text } = Typography;

const OwnerReportPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    // Проверяем роль пользователя
    if (user && user.role !== ROLES.OWNER) {
      setAccessDenied(true);
    }
  }, [user]);

  if (accessDenied) {
    return (
      <div style={{ maxWidth: 600, margin: '0 auto', padding: '40px 20px' }}>
        <Card>
          <Alert
            message="Доступ запрещен"
            description="У вас нет прав для просмотра отчёта собственника. Только владельцы (Owner) могут получить доступ к этому разделу."
            type="error"
            showIcon
            style={{ marginBottom: 24 }}
          />
          <div style={{ textAlign: 'center' }}>
            <Button type="primary" onClick={() => navigate(ROUTES.OVERVIEW)}>
              Вернуться в обзор
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>Отчёт собственника</Title>
      <Text type="secondary">Полная статистика и анализ прибыли</Text>
      <Card style={{ marginTop: 16 }}>
        <Spin spinning={loading}>
          <Empty description="Раздел в разработке. API интеграция будет добавлена в следующем обновлении." />
        </Spin>
      </Card>
    </div>
  );
};

export default OwnerReportPage;
