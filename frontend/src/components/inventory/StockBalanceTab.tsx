import { useEffect, useState } from 'react';
import { Table, Card, Button, Select, Space, Tag, Empty, Spin, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { inventoryApi, InventoryBalanceResponse } from '../../api/inventory';
import { getLocations } from '../../api/business';
import type { Location } from '@/types/api';
import IngredientLoadModal from './IngredientLoadModal';

interface StockBalanceTabProps {
  onRefresh?: () => void;
}

const StockBalanceTab = ({ onRefresh }: StockBalanceTabProps) => {
  const [loading, setLoading] = useState(false);
  const [balance, setBalance] = useState<InventoryBalanceResponse[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocationId, setSelectedLocationId] = useState<number | undefined>(undefined);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    loadLocations();
    loadBalance();
  }, []);

  useEffect(() => {
    loadBalance();
  }, [selectedLocationId]);

  const loadLocations = async () => {
    try {
      const response = await getLocations();
      setLocations(Array.isArray(response.data) ? response.data : []);
    } catch (error: any) {
      console.error('Ошибка загрузки локаций:', error);
    }
  };

  const loadBalance = async () => {
    setLoading(true);
    try {
      const data = await inventoryApi.getInventoryBalance(selectedLocationId);
      setBalance(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки остатков');
    } finally {
      setLoading(false);
    }
  };

  const handleModalSuccess = () => {
    setModalOpen(false);
    loadBalance();
    if (onRefresh) onRefresh();
  };

  // Вычисление статуса и дней до окончания
  const getStatus = (item: InventoryBalanceResponse): { status: 'ok' | 'warning' | 'critical'; daysLeft: number | null } => {
    let daysLeft: number | null = null;
    
    // Вычисляем средний расход в день (используем total_used за все время)
    // Для упрощения используем 30 дней как период для расчета среднего расхода
    const avgDailyUsage = item.total_used / 30; // Упрощенный расчет
    
    if (avgDailyUsage > 0) {
      daysLeft = Math.floor(item.balance / avgDailyUsage);
    }

    // Определяем статус
    let status: 'ok' | 'warning' | 'critical' = 'ok';
    
    if (item.alert_threshold !== null && item.balance <= item.alert_threshold) {
      status = 'critical';
    } else if (item.alert_days_threshold !== null && daysLeft !== null && daysLeft <= item.alert_days_threshold) {
      status = daysLeft <= 3 ? 'critical' : 'warning';
    }

    return { status, daysLeft };
  };

  const columns = [
    {
      title: 'Ингредиент',
      dataIndex: 'display_name_ru',
      key: 'display_name_ru',
      width: 200,
    },
    {
      title: 'Остаток',
      dataIndex: 'balance',
      key: 'balance',
      width: 120,
      render: (value: number, record: InventoryBalanceResponse) => {
        return `${value.toFixed(2)} ${record.unit_ru || record.unit}`;
      },
    },
    {
      title: 'Ед',
      dataIndex: 'unit_ru',
      key: 'unit_ru',
      width: 80,
      render: (value: string, record: InventoryBalanceResponse) => value || record.unit,
    },
    {
      title: 'Расход/день',
      key: 'daily_usage',
      width: 120,
      render: (_: any, record: InventoryBalanceResponse) => {
        const avgDailyUsage = record.total_used / 30; // Упрощенный расчет
        return `${avgDailyUsage.toFixed(2)} ${record.unit_ru || record.unit}`;
      },
    },
    {
      title: 'Осталось дней',
      key: 'days_left',
      width: 130,
      render: (_: any, record: InventoryBalanceResponse) => {
        const { daysLeft } = getStatus(record);
        return daysLeft !== null ? `${daysLeft} дней` : '-';
      },
    },
    {
      title: 'Статус',
      key: 'status',
      width: 150,
      render: (_: any, record: InventoryBalanceResponse) => {
        const { status } = getStatus(record);
        const color = status === 'ok' ? 'success' : status === 'warning' ? 'warning' : 'error';
        const text = status === 'ok' ? '✅ ОК' : status === 'warning' ? '🟡 Предупреждение' : '🔴 Критично';
        return <Tag color={color}>{text}</Tag>;
      },
    },
  ];

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Select
            placeholder="Фильтр: локация"
            allowClear
            style={{ width: 200 }}
            value={selectedLocationId}
            onChange={setSelectedLocationId}
          >
            {locations.map(loc => (
              <Select.Option key={loc.id} value={loc.id}>
                {loc.name}
              </Select.Option>
            ))}
          </Select>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            Добавить загрузку
          </Button>
        </Space>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : balance.length > 0 ? (
          <Table
            dataSource={balance}
            columns={columns}
            rowKey={(record) => `${record.ingredient_code}-${record.location_id}`}
            pagination={{ pageSize: 50 }}
          />
        ) : (
          <Empty description="Нет данных об остатках" />
        )}
      </Card>

      <IngredientLoadModal
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
};

export default StockBalanceTab;
