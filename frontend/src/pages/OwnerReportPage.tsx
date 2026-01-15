import { useEffect, useState } from 'react';
import { Spin, Result, Button, Typography, Card, Row, Col, Table, Space, Statistic } from 'antd';
import { DollarOutlined, CreditCardOutlined, ShoppingOutlined, LineChartOutlined } from '@ant-design/icons';
import apiClient from '../api/client';

const { Paragraph, Title, Text } = Typography;

type LoadState =
  | { kind: 'loading' }
  | { kind: 'forbidden' }
  | { kind: 'unauthorized' }
  | { kind: 'error'; message?: string }
  | { kind: 'ok'; data: any };

interface OwnerReportData {
  period_start: string;
  period_end: string;
  revenue_gross: number;
  fees_total: number;
  expenses_total: number;
  net_profit: number;
  transactions_count: number;
}

// Форматирование как RUB
const formatRub = (value: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

export default function OwnerReportPage() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' });

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        const res = await apiClient.get('/analytics/owner-report');
        if (!alive) return;
        setState({ kind: 'ok', data: res.data });
      } catch (e: any) {
        if (!alive) return;
        const status = e?.response?.status;

        if (status === 401) {
          setState({ kind: 'unauthorized' });
          window.location.href = '/login';
          return;
        }
        if (status === 403) {
          setState({ kind: 'forbidden' });
          return;
        }
        setState({ kind: 'error', message: e?.message });
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  if (state.kind === 'loading') {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (state.kind === 'forbidden') {
    return (
      <Result
        status="403"
        title="Доступ запрещен"
        subTitle="Отчёт собственника доступен только роли owner."
        extra={[
          <Button key="overview" type="primary" onClick={() => (window.location.href = '/overview')}>
            В обзор
          </Button>,
        ]}
      />
    );
  }

  if (state.kind === 'error') {
    return (
      <Result
        status="error"
        title="Ошибка загрузки"
        subTitle={state.message || 'Не удалось получить данные отчёта.'}
        extra={[
          <Button key="retry" type="primary" onClick={() => window.location.reload()}>
            Повторить
          </Button>,
        ]}
      />
    );
  }

  if (state.kind === 'ok') {
    const data: OwnerReportData = state.data;
    
    // Таблица итогов
    const tableColumns = [
      {
        title: 'Параметр',
        dataIndex: 'param',
        key: 'param',
      },
      {
        title: 'Значение',
        dataIndex: 'value',
        key: 'value',
        align: 'right' as const,
      },
    ];

    const tableData = [
      {
        key: 'period',
        param: 'Период',
        value: `${data.period_start} — ${data.period_end}`,
      },
      {
        key: 'transactions',
        param: 'Количество транзакций',
        value: data.transactions_count.toLocaleString('ru-RU'),
      },
      {
        key: 'margin',
        param: 'Маржа (%)' ,
        value: data.revenue_gross > 0 
          ? ((data.net_profit / data.revenue_gross) * 100).toFixed(2)
          : '0.00',
      },
    ];

    return (
      <div style={{ padding: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Title level={2}>Отчёт собственника</Title>
            <Paragraph type="secondary">
              Финансовые метрики за период {data.period_start} — {data.period_end}
            </Paragraph>
          </div>

          {/* 4 карточки с ключевыми метриками */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card hoverable>
                <Statistic
                  title="Выручка"
                  value={data.revenue_gross}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<DollarOutlined />}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card hoverable>
                <Statistic
                  title="Комиссии и налоги"
                  value={data.fees_total}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<CreditCardOutlined />}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card hoverable>
                <Statistic
                  title="Расходы"
                  value={data.expenses_total}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<ShoppingOutlined />}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card hoverable style={{
                background: data.net_profit >= 0 ? '#f0f7ff' : '#fef0f0'
              }}>
                <Statistic
                  title="Чистая прибыль"
                  value={data.net_profit}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<LineChartOutlined />}
                  valueStyle={{ color: data.net_profit >= 0 ? '#1890ff' : '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Таблица дополнительных данных */}
          <Card title="Итоги">
            <Table
              columns={tableColumns}
              dataSource={tableData}
              pagination={false}
              bordered
              size="middle"
            />
          </Card>
        </Space>
      </div>
    );
  }

  return null;
}
