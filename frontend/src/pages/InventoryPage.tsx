import { useEffect, useState } from 'react';
import { Card, Typography, Table, DatePicker, Button, Empty, message, Spin, Switch, Input } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { transactionsApi, Transaction } from '../api/transactions';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const InventoryPage = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs()
  ]);
  const [onlyPositive, setOnlyPositive] = useState(true);
  const [termIdFilter, setTermIdFilter] = useState<string>('');

  const fetchTransactions = async (currentPage: number = page) => {
    setLoading(true);
    try {
      const data = await transactionsApi.getTransactions({
        period_start: dateRange[0].format('YYYY-MM-DD'),
        period_end: dateRange[1].format('YYYY-MM-DD'),
        only_positive: onlyPositive,
        term_id: termIdFilter ? parseInt(termIdFilter) : undefined,
        page: currentPage,
        page_size: pageSize,
      });
      setTransactions(data.items);
      setTotal(data.total);
      setPage(data.page);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки транзакций');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions(1);
  }, []);

  const columns = [
    {
      title: 'Дата/время',
      dataIndex: 'tx_time',
      key: 'tx_time',
      render: (value: string | null) => value ? dayjs(value).format('DD.MM.YY HH:mm') : '-',
    },
    {
      title: 'Терминал',
      dataIndex: 'term_id',
      key: 'term_id',
    },
    {
      title: 'Сумма',
      dataIndex: 'sum_rub',
      key: 'sum_rub',
      render: (value: number) => `${value.toFixed(2)} ₽`,
    },
    {
      title: 'Кнопка',
      dataIndex: 'machine_item_id',
      key: 'machine_item_id',
      render: (value: number | null) => value ?? '-',
    },
    {
      title: 'Комментарий',
      dataIndex: 'terminal_comment',
      key: 'terminal_comment',
      ellipsis: true,
    },
  ];

  return (
    <div>
      <Title level={2}>📦 Склад / Транзакции</Title>
      <Text type="secondary">Детальный список транзакций</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
          />
          <Input
            placeholder="ID терминала"
            value={termIdFilter}
            onChange={(e) => setTermIdFilter(e.target.value)}
            style={{ width: 120 }}
          />
          <div>
            <Text style={{ marginRight: 8 }}>Только продажи:</Text>
            <Switch checked={onlyPositive} onChange={setOnlyPositive} />
          </div>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={() => fetchTransactions(1)}
            loading={loading}
          >
            Обновить
          </Button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : transactions.length > 0 ? (
          <Table
            dataSource={transactions}
            columns={columns}
            rowKey="id"
            pagination={{
              current: page,
              pageSize: pageSize,
              total: total,
              onChange: (newPage) => fetchTransactions(newPage),
              showTotal: (total) => `Всего: ${total}`,
            }}
          />
        ) : (
          <Empty description="Нет транзакций за выбранный период." />
        )}
      </Card>
    </div>
  );
};

export default InventoryPage;
