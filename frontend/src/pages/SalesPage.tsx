import { useEffect, useState } from 'react';
import { Card, Typography, Table, DatePicker, Button, Empty, message, Spin } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { terminalsApi, Terminal } from '../api/terminals';
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

  useEffect(() => {
    fetchTerminals();
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
    </div>
  );
};

export default SalesPage;
