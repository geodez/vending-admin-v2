import { useEffect, useState } from 'react';
import { Spin, Result, Button, Typography, Card, Row, Col, Table, Space, Statistic, Alert, Modal, message, Tooltip } from 'antd';
import { DollarOutlined, CreditCardOutlined, ShoppingOutlined, LineChartOutlined, ReloadOutlined, CheckCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';
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
      const res = await apiClient.get('/sync/health');
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
          const res = await apiClient.post('/sync/sync');
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
        render: (text: string, record: any) => {
          if (record.key === 'margin') {
            return (
              <Space>
                {text}
                <Tooltip title={
                  <div>
                    <div><strong>Маржа прибыли</strong></div>
                    <div style={{ marginTop: 8 }}>
                      Процент чистой прибыли от выручки.
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <strong>Формула:</strong> (Чистая прибыль / Выручка) × 100%
                    </div>
                    <div style={{ marginTop: 4, fontSize: '12px', color: '#999' }}>
                      Показывает эффективность бизнеса
                    </div>
                  </div>
                }>
                  <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                </Tooltip>
              </Space>
            );
          }
          if (record.key === 'transactions') {
            return (
              <Space>
                {text}
                <Tooltip title={
                  <div>
                    <div><strong>Количество транзакций</strong></div>
                    <div style={{ marginTop: 8 }}>
                      Общее количество успешных продаж за период.
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <strong>Источник:</strong> COUNT(*) из vw_owner_report_daily
                    </div>
                    <div style={{ marginTop: 4, fontSize: '12px', color: '#999' }}>
                      Учитываются только транзакции с суммой > 0
                    </div>
                  </div>
                }>
                  <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                </Tooltip>
              </Space>
            );
          }
          return text;
        },
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
            <Space align="center" style={{ marginBottom: 8 }}>
              <Title level={2} style={{ margin: 0 }}>Отчёт собственника</Title>
              <Tooltip title={
                <div style={{ maxWidth: '350px' }}>
                  <div><strong>Источник данных</strong></div>
                  <div style={{ marginTop: 8, fontSize: '12px' }}>
                    Данные рассчитываются из транзакций Vendista через систему шаблонов матриц:
                  </div>
                  <div style={{ marginTop: 8, fontSize: '12px', paddingLeft: '8px' }}>
                    • Транзакции → vw_tx_cogs (с COGS)<br/>
                    • Агрегация → vw_kpi_daily<br/>
                    • Итоговый отчёт → vw_owner_report_daily
                  </div>
                  <div style={{ marginTop: 8, fontSize: '11px', color: '#999' }}>
                    Связь транзакций с напитками происходит через шаблоны матриц (раздел "Шаблоны матриц")
                  </div>
                </div>
              }>
                <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help', fontSize: '18px' }} />
              </Tooltip>
            </Space>
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
                  title={
                    <Space>
                      Выручка
                      <Tooltip title={
                        <div style={{ maxWidth: '350px' }}>
                          <div><strong>Выручка (валовая)</strong></div>
                          <div style={{ marginTop: 8 }}>
                            Сумма всех продаж за период из транзакций Vendista.
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <strong>Формула:</strong> SUM(revenue) из vw_owner_report_daily
                          </div>
                          <div style={{ marginTop: 8, fontSize: '12px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Расчет revenue:</div>
                            <div style={{ marginLeft: '8px' }}>
                              • Из транзакций: (payload->>'sum') / 100<br/>
                              • Конвертация из копеек в рубли<br/>
                              • Агрегация по датам и локациям
                            </div>
                          </div>
                          <div style={{ marginTop: 4, fontSize: '11px', color: '#999' }}>
                            Данные берутся из view vw_tx_cogs → vw_kpi_daily → vw_owner_report_daily
                          </div>
                        </div>
                      }>
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
                  value={data.revenue_gross}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<DollarOutlined />}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card hoverable>
                <Statistic
                  title={
                    <Space>
                      Комиссии и налоги
                      <Tooltip title={
                        <div style={{ maxWidth: '300px' }}>
                          <div><strong>Комиссии платформы</strong></div>
                          <div style={{ marginTop: 8 }}>
                            Комиссия платформы Vendista за обработку платежей.
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <strong>Формула:</strong> Выручка × 8.95%
                          </div>
                          <div style={{ marginTop: 8, fontSize: '12px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Применяется:</div>
                            <div style={{ marginLeft: '8px' }}>
                              • Ко всем транзакциям<br/>
                              • Автоматически при расчете<br/>
                              • Вычитается из выручки
                            </div>
                          </div>
                          <div style={{ marginTop: 4, fontSize: '11px', color: '#999' }}>
                            Стандартная комиссия платформы Vendista
                          </div>
                        </div>
                      }>
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
                  value={data.fees_total}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<CreditCardOutlined />}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Card hoverable>
                <Statistic
                  title={
                    <Space>
                      Расходы
                      <Tooltip title={
                        <div>
                          <div><strong>Переменные расходы</strong></div>
                          <div style={{ marginTop: 8 }}>
                            Переменные расходы, введенные вручную в разделе "Расходы".
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <strong>Формула:</strong> SUM(amount_rub) из variable_expenses
                          </div>
                          <div style={{ marginTop: 8, fontSize: '12px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Включает:</div>
                            <div style={{ marginLeft: '8px' }}>
                              • Аренду помещений<br/>
                              • Коммунальные услуги<br/>
                              • Обслуживание оборудования<br/>
                              • Другие переменные расходы
                            </div>
                          </div>
                          <div style={{ marginTop: 4, fontSize: '11px', color: '#999' }}>
                            Добавляются вручную в разделе "Расходы" за выбранный период
                          </div>
                        </div>
                      }>
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
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
                  title={
                    <Space>
                      Чистая прибыль
                      <Tooltip title={
                        <div style={{ maxWidth: '400px' }}>
                          <div><strong>Чистая прибыль</strong></div>
                          <div style={{ marginTop: 8 }}>
                            Итоговая прибыль после вычета всех расходов.
                          </div>
                          <div style={{ marginTop: 8 }}>
                            <strong>Формула:</strong> Выручка - COGS - Комиссии - Расходы
                          </div>
                          <div style={{ marginTop: 12, padding: '8px', background: '#f5f5f5', borderRadius: '4px', fontSize: '12px' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>COGS (себестоимость):</div>
                            <div style={{ marginLeft: '8px' }}>
                              • Рассчитывается из ингредиентов рецептов напитков<br/>
                              • Только ингредиенты с expense_kind = 'stock_tracked'<br/>
                              • С учетом конвертации единиц:<br/>
                              <div style={{ marginLeft: '12px', marginTop: '4px' }}>
                                - г → кг: qty × (cost / 1000)<br/>
                                - мл → л: qty × (cost / 1000)<br/>
                                - одинаковые единицы: qty × cost
                              </div>
                            </div>
                          </div>
                          <div style={{ marginTop: 8, fontSize: '11px', color: '#999' }}>
                            Данные берутся из view vw_tx_cogs через шаблоны матриц
                          </div>
                        </div>
                      }>
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
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
