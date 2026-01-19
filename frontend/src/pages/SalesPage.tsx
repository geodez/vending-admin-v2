import { useEffect, useState } from 'react';
import { Card, Typography, Table, DatePicker, Button, Empty, message, Spin, Select, Space } from 'antd';
import { SyncOutlined, DownloadOutlined } from '@ant-design/icons';
import { terminalsApi, Terminal } from '../api/terminals';
import { transactionsApi, Transaction } from '../api/transactions';
import { getTerminals, VendistaTerminal } from '../api/sync';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const SalesPage = () => {
  const [terminals, setTerminals] = useState<Terminal[]>([]);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs()
  ]);
  
  // Transactions state
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [dateFrom, setDateFrom] = useState<Dayjs>(dayjs().startOf('month'));
  const [dateTo, setDateTo] = useState<Dayjs>(dayjs());
  const [sumType, setSumType] = useState<'all' | 'positive' | 'non_positive'>('positive');
  const [termIdFilter, setTermIdFilter] = useState<number | undefined>(undefined);
  const [vendistaTerminals, setVendistaTerminals] = useState<VendistaTerminal[]>([]);

  const fetchTerminals = async () => {
    setLoading(true);
    try {
      const data = await terminalsApi.getTerminals(
        dateRange[0].format('YYYY-MM-DD'),
        dateRange[1].format('YYYY-MM-DD')
      );
      setTerminals(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки терминалов');
    } finally {
      setLoading(false);
    }
  };

  const fetchVendistaTerminals = async () => {
    try {
      const { data } = await getTerminals();
      setVendistaTerminals(data);
    } catch (error: any) {
      // Ignore error if terminals not synced yet
      console.error('Error fetching terminals:', error);
    }
  };

  const fetchTransactions = async (currentPage: number = page) => {
    setTransactionsLoading(true);
    try {
      const data = await transactionsApi.getTransactions({
        date_from: dateFrom.format('YYYY-MM-DD'),
        date_to: dateTo.format('YYYY-MM-DD'),
        sum_type: sumType,
        term_id: termIdFilter,
        page: currentPage,
        page_size: pageSize,
      });
      setTransactions(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки транзакций');
    } finally {
      setTransactionsLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await transactionsApi.exportTransactions({
        date_from: dateFrom.format('YYYY-MM-DD'),
        date_to: dateTo.format('YYYY-MM-DD'),
        sum_type: sumType,
        term_id: termIdFilter,
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `transactions_${dateFrom.format('YYYYMMDD')}_${dateTo.format('YYYYMMDD')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('CSV файл загружен');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при экспорте');
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchTerminals();
    fetchVendistaTerminals();
    fetchTransactions(1);
  }, []);

  const columns = [
    {
      title: 'ID Терминала',
      dataIndex: 'term_id',
      key: 'term_id',
      sorter: (a: Terminal, b: Terminal) => a.term_id - b.term_id,
    },
    {
      title: 'Транзакций',
      dataIndex: 'tx_count',
      key: 'tx_count',
      sorter: (a: Terminal, b: Terminal) => a.tx_count - b.tx_count,
    },
    {
      title: 'Выручка (руб)',
      dataIndex: 'revenue_gross',
      key: 'revenue_gross',
      render: (value: number) => value.toFixed(2),
      sorter: (a: Terminal, b: Terminal) => a.revenue_gross - b.revenue_gross,
    },
    {
      title: 'Последняя транзакция',
      dataIndex: 'last_tx_time',
      key: 'last_tx_time',
      render: (value: string | null) => value ? dayjs(value).format('DD.MM.YYYY HH:mm') : '-',
    },
  ];

  return (
    <div>
      <Title level={2}>📊 Продажи по терминалам</Title>
      <Text type="secondary">Статистика продаж по терминалам за период</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
          />
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={fetchTerminals}
            loading={loading}
          >
            Обновить
          </Button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : terminals.length > 0 ? (
          <Table
            dataSource={terminals}
            columns={columns}
            rowKey="term_id"
            pagination={{ pageSize: 20 }}
          />
        ) : (
          <Empty description="Нет данных за выбранный период. Запустите синхронизацию в разделе Настройки." />
        )}
      </Card>

      <Card style={{ marginTop: 16 }} title="Детальный список транзакций">
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Space wrap>
            <DatePicker
              value={dateFrom}
              onChange={(date) => date && setDateFrom(date)}
              format="DD.MM.YYYY"
              placeholder="От"
            />
            <DatePicker
              value={dateTo}
              onChange={(date) => date && setDateTo(date)}
              format="DD.MM.YYYY"
              placeholder="До"
            />
            <Button
              onClick={() => {
                const today = dayjs();
                setDateFrom(today);
                setDateTo(today);
                fetchTransactions(1);
              }}
            >
              Сегодня
            </Button>
            <Button
              onClick={() => {
                const today = dayjs();
                const weekStart = today.startOf('week');
                setDateFrom(weekStart);
                setDateTo(today);
                fetchTransactions(1);
              }}
            >
              Неделя
            </Button>
            <Select
              placeholder="Выберите терминал"
              value={termIdFilter}
              onChange={(value) => setTermIdFilter(value)}
              allowClear
              showSearch
              style={{ width: 250 }}
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={vendistaTerminals.map(t => ({
                value: t.id,
                label: `${t.comment || t.title || `ID: ${t.id}`} (ID: ${t.id})`
              }))}
            />
            <Select
              value={sumType}
              onChange={setSumType}
              style={{ width: 140 }}
              options={[
                { label: 'Все', value: 'all' },
                { label: 'Продажи', value: 'positive' },
                { label: 'Возвраты', value: 'non_positive' },
              ]}
            />
            <Button
              type="primary"
              icon={<SyncOutlined />}
              onClick={() => fetchTransactions(1)}
              loading={transactionsLoading}
            >
              Обновить
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              loading={exporting}
              disabled={transactions.length === 0}
            >
              CSV
            </Button>
          </Space>
          <Text type="secondary">
            Найдено: {total} {total % 10 === 1 && total % 100 !== 11 ? 'транзакция' : 'транзакций'}
            {totalPages > 1 && ` (стр. ${page}/${totalPages})`}
          </Text>
        </Space>

        {transactionsLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : transactions.length > 0 ? (
          <Table
            dataSource={transactions}
            columns={transactionColumns}
            rowKey="id"
            pagination={{
              current: page,
              pageSize: pageSize,
              total: total,
              totalBoundaryShowSizeChanger: false,
              onChange: (newPage) => fetchTransactions(newPage),
              showTotal: (total) => `Всего: ${total}`,
            }}
            scroll={{ x: 1000 }}
          />
        ) : (
          <Empty description="Нет транзакций за выбранный период." />
        )}
      </Card>
    </div>
  );
};

const transactionColumns = [
  {
    title: 'Дата/время',
    dataIndex: 'tx_time',
    key: 'tx_time',
    render: (value: string | null) => {
      if (!value) return '-';
      // Время приходит в формате ISO с timezone (например, "2026-01-19T08:56:34.280+00:00")
      // dayjs автоматически конвертирует в локальный часовой пояс браузера
      // Но нужно убедиться, что время правильно парсится
      const time = dayjs(value);
      return time.format('DD.MM.YY HH:mm');
    },
    width: 140,
    fixed: 'left' as const,
  },
  {
    title: 'Терминал',
    dataIndex: 'term_id',
    key: 'term_id',
    width: 120,
  },
  {
    title: 'Сумма',
    dataIndex: 'sum_rub',
    key: 'sum_rub',
    render: (value: number | null, record: Transaction) => {
      const total = (record.sum_kopecks || 0) / 100;
      return `${total.toFixed(2)} ₽`;
    },
    width: 110,
    align: 'right' as const,
  },
  {
    title: 'Кнопка',
    dataIndex: 'machine_item_id',
    key: 'machine_item_id',
    render: (value: number | null) => value ?? '-',
    width: 90,
    align: 'center' as const,
  },
  {
    title: 'Напиток',
    dataIndex: 'drink_name',
    key: 'drink_name',
    render: (value: string | null) => value || '-',
    width: 200,
    ellipsis: true,
  },
  {
    title: 'Комментарий',
    dataIndex: 'terminal_comment',
    key: 'terminal_comment',
    ellipsis: true,
    render: (value: string | null) => value || '-',
    width: 200,
  },
];

export default SalesPage;
