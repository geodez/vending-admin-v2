import { Card, Row, Col, Statistic, Typography, Alert, Space, Empty } from 'antd';
import {
  DollarOutlined,
  ShoppingCartOutlined,
  RiseOutlined,
  WalletOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { formatCurrency, formatNumber, formatPercent } from '@/utils/formatters';

const { Title, Text } = Typography;

const OverviewPage = () => {
  // Mock data - в реальном приложении данные будут из API
  const kpiData = {
    revenue: 145000,
    sales_count: 1250,
    gross_profit: 95000,
    gross_margin_pct: 65.5,
    variable_expenses: 15000,
    net_profit: 80000,
    net_margin_pct: 55.2,
  };

  const alerts = [
    {
      id: '1',
      type: 'critical' as const,
      message: 'Молоко: осталось 2.5 л (< 3 дней)',
    },
    {
      id: '2',
      type: 'warning' as const,
      message: 'Кофе зерно: осталось 5.2 кг (6 дней)',
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={2}>📊 Обзор</Title>
        <Text type="secondary">Ключевые показатели бизнеса</Text>
      </div>

      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Выручка"
              value={kpiData.revenue}
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
              value={kpiData.sales_count}
              formatter={(value) => formatNumber(Number(value))}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Валовая прибыль"
              value={kpiData.gross_profit}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<RiseOutlined />}
              suffix={
                <Text type="secondary" style={{ fontSize: 14 }}>
                  ({formatPercent(kpiData.gross_margin_pct)})
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
              value={kpiData.variable_expenses}
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
              value={kpiData.net_profit}
              formatter={(value) => formatCurrency(Number(value))}
              prefix={<TrophyOutlined />}
              suffix={
                <Text type="secondary" style={{ fontSize: 14 }}>
                  ({formatPercent(kpiData.net_margin_pct)})
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
                message={alert.message}
                type={alert.type === 'critical' ? 'error' : 'warning'}
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
