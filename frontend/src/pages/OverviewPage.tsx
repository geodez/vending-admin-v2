import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Alert, Space, Empty, Spin, Tabs, message } from 'antd';
import {
  DollarOutlined,
  ShoppingCartOutlined,
  RiseOutlined,
  WalletOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { formatCurrency, formatNumber, formatPercent } from '@/utils/formatters';
import { getOverview, getAlerts } from '../api/analytics';
import { useAuthStore } from '../store/authStore';
import OwnerReportTab from '../components/analytics/OwnerReportTab';

const { Title, Text } = Typography;

const OverviewPage = () => {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [kpiData, setKpiData] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Загружаем KPI для вкладки "Обзор"
      const [kpiResponse, alertsResponse] = await Promise.all([
        getOverview({
          from_date: new Date(new Date().setDate(1)).toISOString().split('T')[0], // Начало месяца
          to_date: new Date().toISOString().split('T')[0], // Сегодня
        }),
        getAlerts().catch(() => ({ data: { alerts: [], summary: {} } })), // Игнорируем ошибки если нет доступа
      ]);

      setKpiData(kpiResponse.data);
      setAlerts(alertsResponse.data?.alerts || []);
    } catch (error: any) {
      console.error('Error loading overview data:', error);
      message.error(error.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={2}>📊 Аналитика</Title>
        <Text type="secondary">Обзор показателей и отчёт собственника</Text>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: 'Обзор',
            children: <OverviewTab kpiData={kpiData} alerts={alerts} />,
          },
          ...(user?.role === 'owner' ? [{
            key: 'owner-report',
            label: 'Отчёт собственника',
            children: <OwnerReportTab />,
          }] : []),
        ]}
      />
    </Space>
  );
};

// Компонент вкладки "Обзор"
const OverviewTab = ({ kpiData, alerts }: { kpiData: any; alerts: any[] }) => {
  if (!kpiData) {
    return <Empty description="Нет данных для отображения" />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Выручка"
              value={kpiData.total_revenue || 0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Количество продаж"
              value={kpiData.total_sales || 0}
              formatter={(value) => formatNumber(Number(value))}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Валовая прибыль"
              value={kpiData.total_gross_profit || 0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<RiseOutlined />}
              suffix={
                <Text type="secondary" style={{ fontSize: 14 }}>
                  ({formatPercent(kpiData.gross_margin_pct || 0)})
                </Text>
              }
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Переменные расходы"
              value={kpiData.total_variable_expenses || 0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<WalletOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Чистая прибыль"
              value={kpiData.net_profit || 0}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<TrophyOutlined />}
              suffix={
                <Text type="secondary" style={{ fontSize: 14 }}>
                  ({formatPercent(kpiData.net_margin_pct || 0)})
                </Text>
              }
              valueStyle={{ color: '#3f8600', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card title="⚠️ Критические алерты">
          <Space direction="vertical" style={{ width: '100%' }}>
            {alerts.map((alert) => (
              <Alert
                key={alert.id}
                message={alert.message || alert.title}
                type={alert.severity === 'critical' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'}
                showIcon
              />
            ))}
          </Space>
        </Card>
      )}

      {/* Chart Placeholder */}
      <Card title="📈 График продаж">
        <Empty description="График будет доступен после интеграции с API" />
      </Card>
    </Space>
  );
};

export default OverviewPage;
