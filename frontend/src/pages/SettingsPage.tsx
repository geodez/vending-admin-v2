import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Empty, message, Spin, Tag, DatePicker, Space, Popconfirm } from 'antd';
import { SyncOutlined, CheckCircleOutlined, CloseCircleOutlined, RedoOutlined } from '@ant-design/icons';
import { getSyncRuns, checkSyncHealth, triggerSyncWithPeriod, rerunSync, SyncRun } from '../api/sync';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;

const SettingsPage = () => {
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [rerunningId, setRerunningId] = useState<number | null>(null);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [dateFrom, setDateFrom] = useState<Dayjs | null>(dayjs().startOf('month'));
  const [dateTo, setDateTo] = useState<Dayjs | null>(dayjs());

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await getSyncRuns({
        date_from: dateFrom ? dateFrom.format('YYYY-MM-DD') : undefined,
        date_to: dateTo ? dateTo.format('YYYY-MM-DD') : undefined,
        limit: 50,
      });
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
        period_start: dateFrom ? dateFrom.format('YYYY-MM-DD') : undefined,
        period_end: dateTo ? dateTo.format('YYYY-MM-DD') : undefined,
      });
      message.success(`Синхронизация завершена: ${data.inserted} новых записей`);
      fetchRuns();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка синхронизации');
    } finally {
      setSyncing(false);
    }
  };

  const handleRerun = async (runId: number) => {
    setRerunningId(runId);
    try {
      const { data } = await rerunSync(runId);
      message.success(`Переза пуск завершен: ${data.inserted} записей`);
      fetchRuns();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка перезапуска');
    } finally {
      setRerunningId(null);
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
      width: 130,
    },
    {
      title: 'Период',
      key: 'period',
      render: (_: any, record: SyncRun) => {
        if (!record.period_start || !record.period_end) return '-';
        return `${dayjs(record.period_start).format('DD.MM')} - ${dayjs(record.period_end).format('DD.MM')}`;
      },
      width: 120,
    },
    {
      title: 'Ожидалось',
      dataIndex: 'expected_total',
      key: 'expected_total',
      render: (value: number | null) => value ?? '-',
      width: 80,
    },
    {
      title: 'Получено',
      dataIndex: 'fetched',
      key: 'fetched',
      render: (value: number | null) => value ?? '-',
      width: 80,
    },
    {
      title: 'Новых',
      dataIndex: 'inserted',
      key: 'inserted',
      render: (value: number | null) => value ?? '-',
      width: 70,
    },
    {
      title: 'Страниц',
      dataIndex: 'pages_fetched',
      key: 'pages_fetched',
      render: (value: number | null) => value ?? '-',
      width: 70,
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
      width: 90,
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: SyncRun) => (
        <Popconfirm
          title="Повторить синхронизацию?"
          description={`Будут использованы параметры: ${dayjs(record.period_start).format('DD.MM.YYYY')} - ${dayjs(record.period_end).format('DD.MM.YYYY')}`}
          onConfirm={() => handleRerun(record.id)}
          okText="Да"
          cancelText="Нет"
        >
          <Button
            type="text"
            size="small"
            icon={<RedoOutlined />}
            loading={rerunningId === record.id}
          >
            Повтор
          </Button>
        </Popconfirm>
      ),
      width: 80,
    },
  ];

  return (
    <div>
      <Title level={2}>⚙️ Настройки / Синхронизация</Title>
      <Text type="secondary">Управление синхронизацией с Vendista</Text>
      
      <Card style={{ marginTop: 16 }} title="Управление">
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Space wrap>
            <Button
              onClick={handleCheckHealth}
              icon={healthOk === null ? undefined : healthOk ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            >
              Проверить соединение
            </Button>
            <DatePicker
              value={dateFrom}
              onChange={(date) => setDateFrom(date)}
              format="DD.MM.YYYY"
              placeholder="От"
            />
            <DatePicker
              value={dateTo}
              onChange={(date) => setDateTo(date)}
              format="DD.MM.YYYY"
              placeholder="До"
            />
            <Button
              type="primary"
              icon={<SyncOutlined spin={syncing} />}
              onClick={handleRunSync}
              loading={syncing}
            >
              Запустить синхронизацию
            </Button>
          </Space>
        </Space>
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
            scroll={{ x: 1000 }}
          />
        ) : (
          <Empty description="Нет истории запусков синхронизации." />
        )}
      </Card>
    </div>
  );
};

export default SettingsPage;
