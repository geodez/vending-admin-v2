import { useEffect, useState } from 'react';
import { Spin, Result, Button, Typography, Card, Row, Col, Table, Space, Statistic, Alert, Modal, message } from 'antd';
import { DollarOutlined, CreditCardOutlined, ShoppingOutlined, LineChartOutlined, ReloadOutlined, CheckCircleOutlined } from '@ant-design/icons';
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
  const [healthLoading, setHealthLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean; status: string } | null>(null);

  // Загрузка данных отчёта
  const loadReport = async () => {
    try {
      const res = await apiClient.get('/analytics/owner-report');
      setState({ kind: 'ok', data: res.data });
    } catch (e: any) {
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
  };

  useEffect(() => {
    let alive = true;

    (async () => {
      if (alive) {
        await loadReport();
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  // Проверка соединения с Vendista API
  const handleCheckHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await apiClient.get('/api/v1/sync/health');
      const { ok, status } = res.data;
      setHealthStatus({ ok, status });
      
      if (ok) {
        message.success('✅ ' + status);
      } else {
        message.error('❌ ' + status);
      }
    } catch (e: any) {
      message.error('Ошибка проверки соединения: ' + (e?.message || 'Unknown error'));
      setHealthStatus({ ok: false, status: e?.message || 'Connection failed' });
    } finally {
      setHealthLoading(false);
    }
  };

  // Запуск синхронизации
  const handleRunSync = async () => {
    Modal.confirm({
      title: 'Запустить синхронизацию',
      content: 'Это может занять некоторое время. Продолжить?',
      okText: 'Да',
      cancelText: 'Отмена',
      onOk: async () => {
        setSyncLoading(true);
        try {
          const res = await apiClient.post('/api/v1/sync/sync');
          const { ok, transactions_synced, message: msg } = res.data;
          
          if (ok) {
            message.success(`✅ Синхронизировано ${transactions_synced} транзакций`);
            // Перезагрузить отчёт
            await loadReport();
          } else {
            message.error('❌ ' + msg);
          }
        } catch (e: any) {
          message.error('Ошибка синхронизации: ' + (e?.message || 'Unknown error'));
        } finally {
          setSyncLoading(false);
        }
      },
    });
  };

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
    const isDataEmpty = data.revenue_gross === 0 && data.transactions_count === 0;
    
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

          {/* Alert если данные нулевые */}
          {isDataEmpty && (
            <Alert
              message="Данные отсутствуют"
              description="В базе данных нет информации о транзакциях. Запустите синхронизацию с API Vendista."
              type="warning"
              showIcon
              closable
            />
          )}

          {/* Кнопки управления синхронизацией */}
          <Card style={{ background: '#f5f5f5' }}>
            <Space>
              <Button
                icon={<CheckCircleOutlined />}
                onClick={handleCheckHealth}
                loading={healthLoading}
              >
                Проверить соединение с Vendista
              </Button>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={handleRunSync}
                loading={syncLoading}
              >
                Запустить синхронизацию
              </Button>
            </Space>
            {healthStatus && (
              <Paragraph style={{ marginTop: 12 }}>
                {healthStatus.ok ? (
                  <span style={{ color: 'green' }}>✅ {healthStatus.status}</span>
                ) : (
                  <span style={{ color: 'red' }}>❌ {healthStatus.status}</span>
                )}
              </Paragraph>
            )}
          </Card>

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
