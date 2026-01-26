import { useEffect, useState } from 'react';
import { Table, Card, Button, Select, DatePicker, Space, Empty, Spin, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { inventoryApi, IngredientLoadResponse } from '../../api/inventory';
import { getLocations } from '../../api/business';
import { getIngredients } from '../../api/business';
import type { Location, Ingredient } from '@/types/api';
import dayjs, { Dayjs } from 'dayjs';
import IngredientLoadModal from './IngredientLoadModal';

const { RangePicker } = DatePicker;

const LoadsHistoryTab = () => {
  const [loading, setLoading] = useState(false);
  const [loads, setLoads] = useState<IngredientLoadResponse[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [selectedLocationId, setSelectedLocationId] = useState<number | undefined>(undefined);
  const [selectedIngredientCode, setSelectedIngredientCode] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ]);
  const [modalOpen, setModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);

  useEffect(() => {
    loadLocations();
    loadIngredients();
    loadLoads();
  }, []);

  useEffect(() => {
    loadLoads();
  }, [selectedLocationId, selectedIngredientCode, dateRange]);

  const loadLocations = async () => {
    try {
      const response = await getLocations();
      setLocations(Array.isArray(response.data) ? response.data : []);
    } catch (error: any) {
      console.error('Ошибка загрузки локаций:', error);
    }
  };

  const loadIngredients = async () => {
    try {
      const response = await getIngredients();
      setIngredients(Array.isArray(response.data) ? response.data : []);
    } catch (error: any) {
      console.error('Ошибка загрузки ингредиентов:', error);
    }
  };

  const loadLoads = async () => {
    setLoading(true);
    try {
      const data = await inventoryApi.getIngredientLoads({
        location_id: selectedLocationId,
        ingredient_code: selectedIngredientCode,
        from_date: dateRange[0].format('YYYY-MM-DD'),
        to_date: dateRange[1].format('YYYY-MM-DD'),
        skip: (page - 1) * pageSize,
        limit: pageSize,
      });
      setLoads(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки истории загрузок');
    } finally {
      setLoading(false);
    }
  };

  const handleModalSuccess = () => {
    setModalOpen(false);
    loadLoads();
  };

  // Получить название ингредиента по коду
  const getIngredientName = (code: string) => {
    const ing = ingredients.find(i => (i.code || i.ingredient_code) === code);
    return ing?.name_ru || ing?.display_name_ru || ing?.name || code;
  };

  // Получить название локации по ID
  const getLocationName = (locationId: number) => {
    const loc = locations.find(l => l.id === locationId);
    return loc?.name || `ID: ${locationId}`;
  };

  const columns = [
    {
      title: 'Дата',
      dataIndex: 'load_date',
      key: 'load_date',
      width: 120,
      render: (value: string) => dayjs(value).format('DD.MM.YY'),
      sorter: (a: IngredientLoadResponse, b: IngredientLoadResponse) =>
        dayjs(a.load_date).unix() - dayjs(b.load_date).unix(),
    },
    {
      title: 'Локация',
      dataIndex: 'location_id',
      key: 'location_id',
      width: 150,
      render: (value: number) => getLocationName(value),
    },
    {
      title: 'Ингредиент',
      dataIndex: 'ingredient_code',
      key: 'ingredient_code',
      width: 200,
      render: (value: string) => getIngredientName(value),
    },
    {
      title: 'Количество',
      key: 'quantity',
      width: 120,
      render: (_: any, record: IngredientLoadResponse) => `${record.qty} ${record.unit}`,
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
      render: (value: string | null) => value || '-',
    },
  ];

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16, flexWrap: 'wrap' }}>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
          />
          <Select
            placeholder="Локация"
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
        ) : loads.length > 0 ? (
          <Table
            dataSource={loads}
            columns={columns}
            rowKey="id"
            pagination={{
              current: page,
              pageSize,
              total: loads.length,
              onChange: setPage,
            }}
          />
        ) : (
          <Empty description="Нет загрузок за выбранный период" />
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

export default LoadsHistoryTab;
