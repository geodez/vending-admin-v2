import { useEffect, useState, useMemo } from 'react';
import { Spin, Result, Button, Typography, Card, Row, Col, Table, Space, Statistic, Alert, Modal, message, Tooltip, DatePicker, Select, Radio } from 'antd';
import { DollarOutlined, CreditCardOutlined, ShoppingOutlined, LineChartOutlined, ReloadOutlined, CheckCircleOutlined, QuestionCircleOutlined, FilterOutlined } from '@ant-design/icons';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import apiClient from '../api/client';
import { getOwnerReport, getDailySales } from '../api/analytics';
import { getTerminals, VendistaTerminal } from '../api/sync';
import dayjs, { Dayjs } from 'dayjs';

const { Paragraph, Title, Text } = Typography;
const { RangePicker } = DatePicker;

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
  avg_check: number;
  gross_profit: number;
  gross_margin_pct: number;
  net_margin_pct: number;
  cogs_total: number;
  top_products: Array<{
    drink_id: number;
    drink_name: string;
    sales_count: number;
    revenue: number;
    cogs: number;
    gross_profit: number;
  }>;
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

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa8c16'];

export default function OwnerReportPage() {
  const [state, setState] = useState<LoadState>({ kind: 'loading' });
  const [healthLoading, setHealthLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<{ ok: boolean; status: string } | null>(null);
  const [dailyData, setDailyData] = useState<any[]>([]);
  const [dailyLoading, setDailyLoading] = useState(false);

  // Filters
  const [periodStart, setPeriodStart] = useState<Dayjs>(dayjs().startOf('month'));
  const [periodEnd, setPeriodEnd] = useState<Dayjs>(dayjs());
  const [selectedTerminal, setSelectedTerminal] = useState<number | undefined>(undefined);
  const [terminals, setTerminals] = useState<VendistaTerminal[]>([]);
  const [terminalsLoading, setTerminalsLoading] = useState(false);

  // Загрузка терминалов
  const loadTerminals = async () => {
    setTerminalsLoading(true);
    try {
      const response = await getTerminals();
      setTerminals(response.data);
    } catch (error: any) {
      console.error('Error loading terminals:', error);
    } finally {
      setTerminalsLoading(false);
    }
  };

  // Загрузка данных отчёта
  const loadReport = async () => {
    try {
      const params: any = {
        period_start: periodStart.format('YYYY-MM-DD'),
        period_end: periodEnd.format('YYYY-MM-DD'),
      };
      if (selectedTerminal) {
        // Find location_id from terminal
        const terminal = terminals.find(t => t.id === selectedTerminal);
        const term: any = terminal;
        if (term?.location_id) {
          params.location_id = term.location_id;
        }
      }

      const res = await getOwnerReport(params);
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

  // Загрузка данных по дням для графиков
  const loadDailyData = async () => {
    setDailyLoading(true);
    try {
      const params: any = {
        from_date: periodStart.format('YYYY-MM-DD'),
        to_date: periodEnd.format('YYYY-MM-DD'),
      };
      if (selectedTerminal) {
        const terminal = terminals.find(t => t.id === selectedTerminal);
        const term: any = terminal;
        if (term?.location_id) {
          params.location_id = term.location_id;
        }
      }

      const res = await getDailySales(params);
      // Группируем по датам (на случай нескольких локаций)
      const grouped = res.data.reduce((acc: any, item: any) => {
        const date = item.date;
        if (!acc[date]) {
          acc[date] = {
            date: date,
            revenue: 0,
            gross_profit: 0,
            net_profit: 0,
            sales_count: 0,
            expenses: 0,
          };
        }
        acc[date].revenue += item.revenue || 0;
        acc[date].gross_profit += item.gross_profit || 0;
        acc[date].sales_count += item.sales_count || 0;
        return acc;
      }, {});

      // Добавляем расходы и считаем чистую прибыль
      const result = Object.values(grouped).map((item: any) => {
        const fees = item.revenue * 0.0895;
        // Расходы нужно получить отдельно, пока используем 0
        const expenses = 0;
        return {
          ...item,
          fees: fees,
          expenses: expenses,
          net_profit: item.gross_profit - fees - expenses,
          dateFormatted: dayjs(item.date).format('DD.MM'),
        };
      }).sort((a: any, b: any) => a.date.localeCompare(b.date));

      setDailyData(result);
    } catch (error: any) {
      console.error('Error loading daily data:', error);
    } finally {
      setDailyLoading(false);
    }
  };

  useEffect(() => {
    loadTerminals();
  }, []);

  useEffect(() => {
    if (terminals.length > 0) {
      loadReport();
      loadDailyData();
    }
  }, [periodStart, periodEnd, selectedTerminal, terminals.length]);

  // Быстрые фильтры периода
  const handleQuickFilter = (type: 'today' | 'week' | 'month' | 'year') => {
    const today = dayjs();
    switch (type) {
      case 'today':
        setPeriodStart(today);
        setPeriodEnd(today);
        break;
      case 'week':
        setPeriodStart(today.startOf('week'));
        setPeriodEnd(today);
        break;
      case 'month':
        setPeriodStart(today.startOf('month'));
        setPeriodEnd(today);
        break;
      case 'year':
        setPeriodStart(today.startOf('year'));
        setPeriodEnd(today);
        break;
    }
  };

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
            await loadReport();
            await loadDailyData();
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
                <Tooltip
                  title={
                    <div style={{ whiteSpace: 'normal', maxWidth: '300px' }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Маржа прибыли</div>
                      <div style={{ marginBottom: '8px' }}>
                        Процент чистой прибыли от выручки.
                      </div>
                      <div style={{ marginBottom: '8px' }}>
                        <strong>Формула:</strong> (Чистая прибыль / Выручка) × 100%
                      </div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        Показывает эффективность бизнеса
                      </div>
                    </div>
                  }
                  overlayStyle={{ maxWidth: '300px' }}
                >
                  <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                </Tooltip>
              </Space>
            );
          }
          if (record.key === 'transactions') {
            return (
              <Space>
                {text}
                <Tooltip
                  title={
                    <div style={{ whiteSpace: 'normal', maxWidth: '300px' }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Количество транзакций</div>
                      <div style={{ marginBottom: '8px' }}>
                        Общее количество успешных продаж за период.
                      </div>
                      <div style={{ marginBottom: '8px' }}>
                        <strong>Источник:</strong> COUNT(*) из vw_owner_report_daily
                      </div>
                      <div style={{ fontSize: '12px', color: '#999' }}>
                        Учитываются только транзакции с суммой {'>'} 0
                      </div>
                    </div>
                  }
                  overlayStyle={{ maxWidth: '300px' }}
                >
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
        key: 'avg_check',
        param: 'Средний чек',
        value: formatRub(data.avg_check || 0),
      },
      {
        key: 'gross_margin',
        param: 'Валовая маржа (%)',
        value: `${data.gross_margin_pct?.toFixed(2) || '0.00'}%`,
      },
      {
        key: 'margin',
        param: 'Маржа (%)',
        value: data.revenue_gross > 0
          ? `${data.net_margin_pct?.toFixed(2) || ((data.net_profit / data.revenue_gross) * 100).toFixed(2)}%`
          : '0.00%',
      },
    ];

    return (
      <div style={{ padding: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Space align="center" style={{ marginBottom: 8 }}>
              <Title level={2} style={{ margin: 0 }}>Отчёт собственника</Title>
              <Tooltip
                title={
                  <div style={{ maxWidth: '350px', whiteSpace: 'normal' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Источник данных</div>
                    <div style={{ marginBottom: '8px', fontSize: '12px' }}>
                      Данные рассчитываются из транзакций Vendista через систему шаблонов матриц:
                    </div>
                    <div style={{ marginBottom: '8px', fontSize: '12px' }}>
                      • Транзакции → vw_tx_cogs (с COGS)
                    </div>
                    <div style={{ marginBottom: '8px', fontSize: '12px' }}>
                      • Агрегация → vw_kpi_daily
                    </div>
                    <div style={{ marginBottom: '8px', fontSize: '12px' }}>
                      • Итоговый отчёт → vw_owner_report_daily
                    </div>
                    <div style={{ fontSize: '11px', color: '#999' }}>
                      Связь транзакций с напитками происходит через шаблоны матриц (раздел "Шаблоны матриц")
                    </div>
                  </div>
                }
                overlayStyle={{ maxWidth: '350px' }}
              >
                <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help', fontSize: '18px' }} />
              </Tooltip>
            </Space>
          </div>

          {/* Фильтры */}
          <Card title={<><FilterOutlined /> Фильтры</>}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong style={{ marginRight: 8 }}>Период:</Text>
                <RangePicker
                  value={[periodStart, periodEnd]}
                  onChange={(dates) => {
                    if (dates && dates[0] && dates[1]) {
                      setPeriodStart(dates[0]);
                      setPeriodEnd(dates[1]);
                    }
                  }}
                  format="DD.MM.YYYY"
                  style={{ marginRight: 16 }}
                />
                <Space>
                  <Button size="small" onClick={() => handleQuickFilter('today')}>Сегодня</Button>
                  <Button size="small" onClick={() => handleQuickFilter('week')}>Неделя</Button>
                  <Button size="small" onClick={() => handleQuickFilter('month')}>Месяц</Button>
                  <Button size="small" onClick={() => handleQuickFilter('year')}>Год</Button>
                </Space>
              </div>
              <div>
                <Text strong style={{ marginRight: 8 }}>Терминал:</Text>
                <Select
                  placeholder="Все терминалы"
                  allowClear
                  style={{ width: 300 }}
                  loading={terminalsLoading}
                  value={selectedTerminal}
                  onChange={setSelectedTerminal}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  options={terminals.map(term => ({
                    value: term.id,
                    label: `${term.comment || term.title || `Терминал #${term.id}`} (ID: ${term.id})`
                  }))}
                />
              </div>
            </Space>
          </Card>

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
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '350px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Выручка (валовая)</div>
                            <div style={{ marginBottom: '8px' }}>
                              Сумма всех продаж за период из транзакций Vendista.
                            </div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> SUM(revenue) из vw_owner_report_daily
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '350px' }}
                      >
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
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '300px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Комиссии платформы</div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> Выручка × 8.95%
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '300px' }}
                      >
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
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '350px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Переменные расходы</div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> SUM(amount_rub) из variable_expenses
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '350px' }}
                      >
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
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '400px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Чистая прибыль</div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> Выручка - COGS - Комиссии - Расходы
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '400px' }}
                      >
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

          {/* Графики */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Динамика выручки и прибыли" loading={dailyLoading}>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="dateFormatted" />
                    <YAxis />
                    <RechartsTooltip formatter={(value: number) => formatRub(value)} />
                    <Legend />
                    <Line type="monotone" dataKey="revenue" stroke="#1890ff" name="Выручка" />
                    <Line type="monotone" dataKey="gross_profit" stroke="#52c41a" name="Валовая прибыль" />
                    <Line type="monotone" dataKey="net_profit" stroke="#722ed1" name="Чистая прибыль" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Количество транзакций" loading={dailyLoading}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="dateFormatted" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="sales_count" fill="#1890ff" name="Транзакции" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {/* Топ продукты */}
          {data.top_products && data.top_products.length > 0 && (
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="Топ-10 продуктов по выручке">
                  <Table
                    dataSource={data.top_products}
                    pagination={false}
                    size="small"
                    columns={[
                      {
                        title: 'Напиток',
                        dataIndex: 'drink_name',
                        key: 'drink_name',
                      },
                      {
                        title: 'Продажи',
                        dataIndex: 'sales_count',
                        key: 'sales_count',
                        align: 'right' as const,
                      },
                      {
                        title: 'Выручка',
                        dataIndex: 'revenue',
                        key: 'revenue',
                        align: 'right' as const,
                        render: (val: number) => formatRub(val),
                      },
                    ]}
                  />
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="Распределение выручки по продуктам">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={data.top_products.slice(0, 8)}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="revenue"
                      >
                        {data.top_products.slice(0, 8).map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <RechartsTooltip formatter={(value: number) => formatRub(value)} />
                    </PieChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>
          )}

          {/* Расширенные метрики */}
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title={
                    <Space>
                      Средний чек
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '350px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Средний чек</div>
                            <div style={{ marginBottom: '8px' }}>
                              Средняя сумма одной транзакции за период.
                            </div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> Выручка / Количество транзакций
                            </div>
                            <div style={{ fontSize: '12px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', marginBottom: '8px' }}>
                              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Пример:</div>
                              <div style={{ marginLeft: '8px' }}>
                                • Выручка: 66 702 ₽
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • Транзакций: 498
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • Средний чек: 66 702 / 498 = 133.94 ₽
                              </div>
                            </div>
                            <div style={{ fontSize: '11px', color: '#999' }}>
                              Показывает среднюю стоимость покупки
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '350px' }}
                      >
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
                  value={data.avg_check || 0}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<DollarOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title={
                    <Space>
                      Валовая прибыль
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '400px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Валовая прибыль</div>
                            <div style={{ marginBottom: '8px' }}>
                              Прибыль до вычета комиссий и переменных расходов.
                            </div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> Выручка - COGS (себестоимость)
                            </div>
                            <div style={{ fontSize: '12px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', marginBottom: '8px' }}>
                              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>COGS включает:</div>
                              <div style={{ marginLeft: '8px' }}>
                                • Стоимость ингредиентов напитков
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • Только ингредиенты с expense_kind = 'stock_tracked'
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • С учетом конвертации единиц (г→кг, мл→л)
                              </div>
                            </div>
                            <div style={{ fontSize: '11px', color: '#999' }}>
                              Валовая прибыль показывает эффективность продаж до учета операционных расходов
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '400px' }}
                      >
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
                  value={data.gross_profit || 0}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<LineChartOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title={
                    <Space>
                      COGS (себестоимость)
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '400px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>COGS (Cost of Goods Sold)</div>
                            <div style={{ marginBottom: '8px' }}>
                              Себестоимость проданных товаров - стоимость ингредиентов, использованных для приготовления напитков.
                            </div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> SUM(стоимость ингредиентов) из всех проданных напитков
                            </div>
                            <div style={{ fontSize: '12px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', marginBottom: '8px' }}>
                              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Расчет COGS:</div>
                              <div style={{ marginLeft: '8px' }}>
                                • Для каждого проданного напитка:
                              </div>
                              <div style={{ marginLeft: '16px', marginTop: '4px' }}>
                                - Берется рецепт напитка (drink_items)
                              </div>
                              <div style={{ marginLeft: '16px' }}>
                                - Для каждого ингредиента:
                              </div>
                              <div style={{ marginLeft: '24px', marginTop: '4px' }}>
                                • qty × cost_per_unit (с конвертацией единиц)
                              </div>
                              <div style={{ marginLeft: '8px', marginTop: '4px' }}>
                                • Учитываются только ингредиенты с expense_kind = 'stock_tracked'
                              </div>
                            </div>
                            <div style={{ fontSize: '12px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', marginBottom: '8px' }}>
                              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Конвертация единиц:</div>
                              <div style={{ marginLeft: '8px' }}>
                                • г → кг: qty × (cost / 1000)
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • мл → л: qty × (cost / 1000)
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • Одинаковые единицы: qty × cost
                              </div>
                            </div>
                            <div style={{ fontSize: '11px', color: '#999' }}>
                              Данные берутся из view vw_tx_cogs через шаблоны матриц
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '400px' }}
                      >
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
                  value={data.cogs_total || 0}
                  formatter={(val) => formatRub(val as number)}
                  prefix={<ShoppingOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title={
                    <Space>
                      Валовая маржа
                      <Tooltip
                        title={
                          <div style={{ maxWidth: '350px', whiteSpace: 'normal' }}>
                            <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>Валовая маржа</div>
                            <div style={{ marginBottom: '8px' }}>
                              Процент валовой прибыли от выручки.
                            </div>
                            <div style={{ marginBottom: '8px' }}>
                              <strong>Формула:</strong> (Валовая прибыль / Выручка) × 100%
                            </div>
                            <div style={{ fontSize: '12px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '4px', marginBottom: '8px' }}>
                              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Показывает:</div>
                              <div style={{ marginLeft: '8px' }}>
                                • Эффективность продаж
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • Насколько выручка превышает себестоимость
                              </div>
                              <div style={{ marginLeft: '8px' }}>
                                • Рентабельность до учета операционных расходов
                              </div>
                            </div>
                            <div style={{ fontSize: '11px', color: '#999' }}>
                              Высокая валовая маржа = хорошая эффективность продаж
                            </div>
                          </div>
                        }
                        overlayStyle={{ maxWidth: '350px' }}
                      >
                        <QuestionCircleOutlined style={{ color: '#1890ff', cursor: 'help' }} />
                      </Tooltip>
                    </Space>
                  }
                  value={data.gross_margin_pct || 0}
                  suffix="%"
                  prefix={<LineChartOutlined />}
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
