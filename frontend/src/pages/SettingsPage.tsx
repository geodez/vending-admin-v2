import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Empty, message, Spin, Tag, DatePicker } from 'antd';
import { SyncOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { getSyncRuns, checkSyncHealth, triggerSyncWithPeriod, SyncRun } from '../api/sync';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const SettingsPage = () => {
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs()
  ]);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await getSyncRuns(20);
      setRuns(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки истории');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckHealth = async () => {
    try {
      const { data } = await checkSyncHealth();
      setHealthOk(data.ok);
      message.success(data.status);
    } catch (error: any) {
      setHealthOk(false);
      message.error(error.response?.data?.detail || 'Ошибка проверки соединения');
    }
  };

  const handleRunSync = async () => {
    setSyncing(true);
    try {
      const { data } = await triggerSyncWithPeriod({
        period_start: dateRange[0].format('YYYY-MM-DD'),
        period_end: dateRange[1].format('YYYY-MM-DD'),
      });
      message.success(`Синхронизация завершена: ${data.inserted} новых записей`);
      fetchRuns();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка синхронизации');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const columns = [
    {
      title: 'Дата/время',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (value: string | null) => value ? dayjs(value).format('DD.MM.YY HH:mm') : '-',
    },
    {
      title: 'Период',
      key: 'period',
      render: (_: any, record: SyncRun) => {
        if (!record.period_start || !record.period_end) return '-';
        return `${dayjs(record.period_start).format('DD.MM')} - ${dayjs(record.period_end).format('DD.MM')}`;
      },
    },
    {
      title: 'Ожидалось',
      dataIndex: 'expected_total',
      key: 'expected_total',
      render: (value: number | null) => value ?? '-',
    },
    {
      title: 'Получено',
      dataIndex: 'fetched',
      key: 'fetched',
      render: (value: number | null) => value ?? '-',
    },
    {
      title: 'Новых',
      dataIndex: 'inserted',
      key: 'inserted',
      render: (value: number | null) => value ?? '-',
    },
    {
      title: 'Страниц',
      dataIndex: 'pages_fetched',
      key: 'pages_fetched',
      render: (value: number | null) => value ?? '-',
    },
    {
      title: 'Статус',
      dataIndex: 'ok',
      key: 'ok',
      render: (value: boolean | null) => {
        if (value === null) return '-';
        return value ? (
          <Tag color="success" icon={<CheckCircleOutlined />}>OK</Tag>
        ) : (
          <Tag color="error" icon={<CloseCircleOutlined />}>FAIL</Tag>
        );
      },
    },
  ];

  return (
    <div>
      <Title level={2}>⚙️ Настройки / Синхронизация</Title>
      <Text type="secondary">Управление синхронизацией с Vendista</Text>
      
      <Card style={{ marginTop: 16 }} title="Управление">
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <Button
            onClick={handleCheckHealth}
            icon={healthOk === null ? undefined : healthOk ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          >
            Проверить соединение
          </Button>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
          />
          <Button
            type="primary"
            icon={<SyncOutlined spin={syncing} />}
            onClick={handleRunSync}
            loading={syncing}
          >
            Запустить синхронизацию
          </Button>
        </div>
      </Card>

      <Card style={{ marginTop: 16 }} title="История запусков">
        <Button
          style={{ marginBottom: 16 }}
          icon={<SyncOutlined />}
          onClick={fetchRuns}
          loading={loading}
        >
          Обновить
        </Button>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : runs.length > 0 ? (
          <Table
            dataSource={runs}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            size="small"
          />
        ) : (
          <Empty description="Нет истории запусков синхронизации." />
        )}
      </Card>
    </div>
  );
};

export default SettingsPage;
