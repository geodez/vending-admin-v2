import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Tabs, Space, Tag, Input, Select, DatePicker, message, Row, Col } from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { inventoryApi, InventoryStatusItem, IngredientLoad } from '../api/inventory';
import { getLocations } from '../api/business';
import { AddLoadModal } from '../components/inventory/AddLoadModal';
import type { Location } from '../types/api';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const InventoryPage = () => {
  const [activeTab, setActiveTab] = useState('stock');
  const [loading, setLoading] = useState(false);
  const [locations, setLocations] = useState<Location[]>([]);

  // Data states
  const [stockItems, setStockItems] = useState<InventoryStatusItem[]>([]);
  const [loadHistory, setLoadHistory] = useState<IngredientLoad[]>([]);

  // Filters
  const [selectedLocation, setSelectedLocation] = useState<number | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().startOf('month'),
    dayjs().endOf('month')
  ]);

  // Modals
  const [addLoadModalVisible, setAddLoadModalVisible] = useState(false);

  useEffect(() => {
    fetchLocations();
  }, []);

  useEffect(() => {
    if (activeTab === 'stock') {
      fetchStockStatus();
    } else {
      fetchLoadHistory();
    }
  }, [activeTab, selectedLocation, dateRange]); // Refetch when filters change

  const fetchLocations = async () => {
    try {
      const response = await getLocations();
      setLocations(Array.isArray(response) ? response : (response as any).data || []);
    } catch (error) {
      console.error('Failed to fetch locations', error);
    }
  };

  const fetchStockStatus = async () => {
    setLoading(true);
    try {
      const data = await inventoryApi.getInventoryStatus({
        location_id: selectedLocation,
      });
      setStockItems(data || []);
    } catch (error) {
      message.error('Ошибка загрузки склада');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLoadHistory = async () => {
    setLoading(true);
    try {
      const data = await inventoryApi.getIngredientLoads({
        location_id: selectedLocation,
        from_date: dateRange ? dateRange[0].format('YYYY-MM-DD') : undefined,
        to_date: dateRange ? dateRange[1].format('YYYY-MM-DD') : undefined,
      });
      setLoadHistory(data || []);
    } catch (error) {
      message.error('Ошибка загрузки истории');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const stockColumns = [
    {
      title: 'Ингредиент',
      dataIndex: 'display_name_ru',
      key: 'name',
      render: (text: string, record: InventoryStatusItem) => (
        <Space direction="vertical" size="small">
          <Text strong>{text || record.ingredient_code}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.ingredient_code}</Text>
        </Space>
      ),
    },
    {
      title: 'Локация',
      dataIndex: 'location_name',
      key: 'location',
    },
    {
      title: 'Загружено',
      dataIndex: 'total_loaded',
      key: 'loaded',
      render: (val: number, record: InventoryStatusItem) => `${val.toFixed(2)} ${record.unit_ru || record.unit}`,
    },
    {
      title: 'Использовано',
      dataIndex: 'total_used',
      key: 'used',
      render: (val: number, record: InventoryStatusItem) => `${val.toFixed(2)} ${record.unit_ru || record.unit}`,
    },
    {
      title: 'Остаток',
      dataIndex: 'balance',
      key: 'balance',
      render: (val: number, record: InventoryStatusItem) => {
        const color = record.is_low_stock ? 'red' : val < 0 ? 'orange' : 'green';
        return (
          <Tag color={color} style={{ fontSize: 14, padding: '4px 8px' }}>
            {val.toFixed(2)} {record.unit_ru || record.unit}
          </Tag>
        );
      },
      sorter: (a: InventoryStatusItem, b: InventoryStatusItem) => a.balance - b.balance,
    },
    {
      title: 'Alert',
      dataIndex: 'alert_threshold',
      key: 'alert',
      render: (val: number | undefined) => val ? `< ${val}` : '-',
    },
  ];

  const historyColumns = [
    {
      title: 'Дата',
      dataIndex: 'load_date',
      key: 'date',
      render: (date: string) => dayjs(date).format('DD.MM.YYYY'),
      sorter: (a: IngredientLoad, b: IngredientLoad) => dayjs(a.load_date).unix() - dayjs(b.load_date).unix(),
    },
    {
      title: 'Локация',
      dataIndex: 'location_map', // We need to map ID to name or use join from backend. Backend returns ID.
      key: 'location',
      render: (_: any, record: IngredientLoad) => {
        const loc = locations.find(l => l.id === record.location_id);
        return loc ? loc.name : `Loc #${record.location_id}`;
      }
    },
    {
      title: 'Ингредиент',
      dataIndex: 'ingredient_code',
      key: 'ingredient',
    },
    {
      title: 'Количество',
      dataIndex: 'qty',
      key: 'qty',
      render: (val: number, record: IngredientLoad) => (
        <Text strong style={{ color: 'green' }}>
          +{val} {record.unit}
        </Text>
      ),
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <Title level={2}>📦 Склад и Инвентаризация</Title>
            <Text type="secondary">Управление остатками ингредиентов и загрузками</Text>
          </div>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => activeTab === 'stock' ? fetchStockStatus() : fetchLoadHistory()}
            >
              Обновить
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setAddLoadModalVisible(true)}
            >
              Загрузить ингредиенты
            </Button>
          </Space>
        </div>

        <Card>
          {/* Filters */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Select
                style={{ width: '100%' }}
                placeholder="Все локации"
                allowClear
                onChange={setSelectedLocation}
                value={selectedLocation}
              >
                {locations.map(loc => (
                  <Select.Option key={loc.id} value={loc.id}>{loc.name}</Select.Option>
                ))}
              </Select>
            </Col>
            {activeTab === 'history' && (
              <Col span={8}>
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => setDateRange(dates as any)}
                  style={{ width: '100%' }}
                />
              </Col>
            )}
          </Row>

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'stock',
                label: 'Текущие остатки',
                children: (
                  <Table
                    dataSource={stockItems}
                    columns={stockColumns}
                    rowKey={(record) => `${record.ingredient_code}_${record.location_id}`}
                    loading={loading}
                    pagination={{ pageSize: 20 }}
                  />
                ),
              },
              {
                key: 'history',
                label: 'История загрузок',
                children: (
                  <Table
                    dataSource={loadHistory}
                    columns={historyColumns}
                    rowKey="id"
                    loading={loading}
                    pagination={{ pageSize: 20 }}
                  />
                ),
              },
            ]}
          />
        </Card>
      </Space>

      <AddLoadModal
        visible={addLoadModalVisible}
        onCancel={() => setAddLoadModalVisible(false)}
        onSuccess={() => {
          setAddLoadModalVisible(false);
          fetchStockStatus();
          fetchLoadHistory();
        }}
      />
    </div>
  );
};

export default InventoryPage;
