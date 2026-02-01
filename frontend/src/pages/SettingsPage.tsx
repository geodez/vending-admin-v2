import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Empty, message, Spin, Tag, DatePicker, Space, Popconfirm, List, Badge, Switch } from 'antd';
import { SyncOutlined, CheckCircleOutlined, CloseCircleOutlined, RedoOutlined, DatabaseOutlined, ReloadOutlined } from '@ant-design/icons';
import { getSyncRuns, checkSyncHealth, triggerSyncWithPeriod, rerunSync, syncTerminals, getTerminals, updateTerminal, SyncRun, VendistaTerminal } from '../api/sync';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;

const SettingsPage = () => {
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncingTerminals, setSyncingTerminals] = useState(false);
  const [rerunningId, setRerunningId] = useState<number | null>(null);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);
  const [dateFrom, setDateFrom] = useState<Dayjs | null>(dayjs().startOf('month'));
  const [dateTo, setDateTo] = useState<Dayjs | null>(dayjs());
  const [terminals, setTerminals] = useState<VendistaTerminal[]>([]);
  const [loadingTerminals, setLoadingTerminals] = useState(false);
  const [terminalUpdating, setTerminalUpdating] = useState<Record<number, boolean>>({});
  // Отдельные даты для фильтрации истории (по умолчанию - без фильтра, показываем все)
  const [historyDateFrom, setHistoryDateFrom] = useState<Dayjs | null>(null);
  const [historyDateTo, setHistoryDateTo] = useState<Dayjs | null>(null);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const data = await getSyncRuns({
        // Используем отдельные даты для истории, если не заданы - показываем все запуски
        date_from: historyDateFrom ? historyDateFrom.format('YYYY-MM-DD') : undefined,
        date_to: historyDateTo ? historyDateTo.format('YYYY-MM-DD') : undefined,
        limit: 50,
      });
      setRuns(data);
    } catch (error: any) {
      console.error('Error fetching sync runs:', error);
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

  const fetchTerminals = async () => {
    setLoadingTerminals(true);
    try {
      const { data } = await getTerminals();
      setTerminals(data);
    } catch (error: any) {
      // Ignore error if terminals not synced yet
      if (error.response?.status !== 404) {
        console.error('Error fetching terminals:', error);
      }
    } finally {
      setLoadingTerminals(false);
    }
  };

  const handleSyncTerminals = async () => {
    setSyncingTerminals(true);
    try {
      const { data } = await syncTerminals();
      if (data.success) {
        message.success(
          `Синхронизация терминалов завершена: ${data.synced_count} терминалов ` +
          `(создано: ${data.created_count}, обновлено: ${data.updated_count})`
        );
        // Refresh terminals list after sync
        await fetchTerminals();
      } else {
        message.error(data.message || 'Ошибка синхронизации терминалов');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка синхронизации терминалов');
    } finally {
      setSyncingTerminals(false);
    }
  };

  const handleToggleTerminal = async (terminal: VendistaTerminal, nextActive: boolean) => {
    setTerminalUpdating(prev => ({ ...prev, [terminal.id]: true }));
    try {
      const { data } = await updateTerminal(terminal.id, { is_active: nextActive });
      setTerminals(prev => prev.map(t => (t.id === terminal.id ? { ...t, is_active: data.is_active } : t)));
      message.success(`Терминал #${terminal.id} ${nextActive ? 'включен' : 'отключен'}`);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка обновления терминала');
    } finally {
      setTerminalUpdating(prev => ({ ...prev, [terminal.id]: false }));
    }
  };

  useEffect(() => {
    fetchRuns();
    fetchTerminals();
  }, []);

  // Автоматически обновляем историю при изменении фильтров
  useEffect(() => {
    fetchRuns();
  }, [historyDateFrom, historyDateTo]);

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
          <Space wrap>
            <Button
              type="default"
              icon={<DatabaseOutlined spin={syncingTerminals} />}
              onClick={handleSyncTerminals}
              loading={syncingTerminals}
            >
              Синхронизировать терминалы
            </Button>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Извлекает терминалы из транзакций и добавляет их в базу данных
            </Text>
          </Space>
        </Space>
      </Card>

      <Card 
        style={{ marginTop: 16 }} 
        title={
          <Space>
            <span>Доступные терминалы</span>
            <Badge count={terminals.length} showZero />
            <Button
              type="text"
              size="small"
              icon={<ReloadOutlined />}
              onClick={fetchTerminals}
              loading={loadingTerminals}
              style={{ marginLeft: 8 }}
            />
          </Space>
        }
      >
        {loadingTerminals ? (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Spin size="small" />
          </div>
        ) : terminals.length > 0 ? (
          <List
            size="small"
            dataSource={terminals}
            renderItem={(terminal) => (
              <List.Item>
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Space>
                    <Text strong>#{terminal.id}</Text>
                    <Text>{terminal.comment || terminal.title || 'Без названия'}</Text>
                    {terminal.title && terminal.title !== terminal.comment && (
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        ({terminal.title})
                      </Text>
                    )}
                  </Space>
                  <Space size="small">
                    <Tag color={terminal.is_active ? 'green' : 'default'}>
                      {terminal.is_active ? 'Активен' : 'Неактивен'}
                    </Tag>
                    <Switch
                      checked={terminal.is_active}
                      loading={terminalUpdating[terminal.id]}
                      onChange={(checked) => handleToggleTerminal(terminal, checked)}
                    />
                  </Space>
                </Space>
              </List.Item>
            )}
          />
        ) : (
          <Empty 
            description="Нет синхронизированных терминалов" 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>

      <Card style={{ marginTop: 16 }} title="История запусков">
        <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
          <Space wrap>
            <DatePicker
              value={historyDateFrom}
              onChange={(date) => setHistoryDateFrom(date)}
              format="DD.MM.YYYY"
              placeholder="От (фильтр истории)"
              allowClear
            />
            <DatePicker
              value={historyDateTo}
              onChange={(date) => setHistoryDateTo(date)}
              format="DD.MM.YYYY"
              placeholder="До (фильтр истории)"
              allowClear
            />
            <Button
              icon={<SyncOutlined />}
              onClick={fetchRuns}
              loading={loading}
            >
              Обновить
            </Button>
            {(historyDateFrom || historyDateTo) && (
              <Button
                type="text"
                size="small"
                onClick={() => {
                  setHistoryDateFrom(null);
                  setHistoryDateTo(null);
                }}
              >
                Сбросить фильтр
              </Button>
            )}
          </Space>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {historyDateFrom || historyDateTo
              ? 'Показаны запуски с фильтром по датам'
              : 'Показаны все запуски синхронизации'}
          </Text>
        </Space>

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
