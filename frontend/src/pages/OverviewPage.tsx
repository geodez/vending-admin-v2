import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Alert, Space, Empty, Spin, Tabs, message } from 'antd';
import {
  DollarOutlined,
  ShoppingCartOutlined,
  RiseOutlined,
  WalletOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatCurrency, formatNumber, formatPercent } from '@/utils/formatters';
import { getOverview, getAlerts, getDailySales } from '../api/analytics';
import { useAuthStore } from '../store/authStore';
import OwnerReportTab from '../components/analytics/OwnerReportTab';
import dayjs from 'dayjs';

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
      const fromDate = dayjs().startOf('month').format('YYYY-MM-DD');
      const toDate = dayjs().format('YYYY-MM-DD');
      
      // Загружаем KPI для вкладки "Обзор"
      const [kpiResponse, alertsResponse] = await Promise.all([
        getOverview({
          from_date: fromDate,
          to_date: toDate,
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
  const [chartData, setChartData] = useState<any[]>([]);
  const [chartLoading, setChartLoading] = useState(false);

  useEffect(() => {
    loadChartData();
  }, []);

  const loadChartData = async () => {
    setChartLoading(true);
    try {
      const fromDate = dayjs().startOf('month').format('YYYY-MM-DD');
      const toDate = dayjs().format('YYYY-MM-DD');
      
      const response = await getDailySales({
        from_date: fromDate,
        to_date: toDate,
      });
      
      // Форматируем данные для графика
      const formatted = response.data.map((item: any) => ({
        date: dayjs(item.date).format('DD.MM'),
        revenue: item.revenue || 0,
        gross_profit: item.gross_profit || 0,
        sales_count: item.sales_count || 0,
      }));
      
      setChartData(formatted);
    } catch (error: any) {
      console.error('Error loading chart data:', error);
    } finally {
      setChartLoading(false);
    }
  };

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
            {alerts.map((alert, index) => (
              <Alert
                key={`${alert.type || 'alert'}-${alert.ingredient_code || alert.drink_id || index}`}
                message={alert.message || alert.title || 'Алерт'}
                type={alert.severity === 'critical' ? 'error' : alert.severity === 'warning' ? 'warning' : 'info'}
                showIcon
              />
            ))}
          </Space>
        </Card>
      )}

      {/* Chart */}
      <Card title="📈 График продаж" loading={chartLoading}>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <RechartsTooltip 
                formatter={(value: number, name: string) => {
                  if (name === 'Выручка' || name === 'Валовая прибыль') {
                    return [formatCurrency(value), name];
                  }
                  return [value, name];
                }}
              />
              <Legend />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="revenue" 
                stroke="#1890ff" 
                name="Выручка"
                strokeWidth={2}
              />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="gross_profit" 
                stroke="#52c41a" 
                name="Валовая прибыль"
                strokeWidth={2}
              />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="sales_count" 
                stroke="#faad14" 
                name="Количество продаж"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <Empty description="Нет данных для графика" />
        )}
      </Card>
    </Space>
  );
};

export default OverviewPage;
