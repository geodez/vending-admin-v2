import { useEffect, useState } from 'react';
import { Table, Card, Select, DatePicker, Space, Empty, Spin, message } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { inventoryApi, IngredientUsageDaily } from '../../api/inventory';
import { getLocations } from '../../api/business';
import { getIngredients } from '../../api/business';
import type { Location, Ingredient } from '@/types/api';
import dayjs, { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

const UsageDailyTab = () => {
  const [loading, setLoading] = useState(false);
  const [usage, setUsage] = useState<IngredientUsageDaily[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [selectedLocationId, setSelectedLocationId] = useState<number | undefined>(undefined);
  const [selectedIngredientCode, setSelectedIngredientCode] = useState<string | undefined>(undefined);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs(),
  ]);

  useEffect(() => {
    loadLocations();
    loadIngredients();
    loadUsage();
  }, []);

  useEffect(() => {
    loadUsage();
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
      const data = Array.isArray(response.data) ? response.data : [];
      setIngredients(data.filter(i => i.expense_kind === 'stock_tracked'));
    } catch (error: any) {
      console.error('Ошибка загрузки ингредиентов:', error);
    }
  };

  const loadUsage = async () => {
    setLoading(true);
    try {
      const data = await inventoryApi.getIngredientUsageDaily({
        location_id: selectedLocationId,
        ingredient_code: selectedIngredientCode,
        from_date: dateRange[0].format('YYYY-MM-DD'),
        to_date: dateRange[1].format('YYYY-MM-DD'),
      });
      setUsage(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки расхода');
    } finally {
      setLoading(false);
    }
  };

  // Подготовка данных для графика
  const chartData = usage.reduce((acc, item) => {
    const day = item.day;
    if (!acc[day]) {
      acc[day] = { day: dayjs(day).format('DD.MM') };
    }
    acc[day][item.ingredient_name] = item.qty_used;
    return acc;
  }, {} as Record<string, any>);

  const chartDataArray = Object.values(chartData).sort((a: any, b: any) =>
    dayjs(a.day, 'DD.MM').unix() - dayjs(b.day, 'DD.MM').unix()
  );

  // Получить уникальные ингредиенты для легенды
  const uniqueIngredients = Array.from(new Set(usage.map(u => u.ingredient_name)));

  const columns = [
    {
      title: 'День',
      dataIndex: 'day',
      key: 'day',
      width: 120,
      render: (value: string) => dayjs(value).format('DD.MM.YY'),
      sorter: (a: IngredientUsageDaily, b: IngredientUsageDaily) =>
        dayjs(a.day).unix() - dayjs(b.day).unix(),
    },
    {
      title: 'Ингредиент',
      dataIndex: 'ingredient_name',
      key: 'ingredient_name',
      width: 200,
    },
    {
      title: 'Расход',
      key: 'qty_used',
      width: 150,
      render: (_: any, record: IngredientUsageDaily) => `${record.qty_used.toFixed(2)} ${record.unit}`,
      sorter: (a: IngredientUsageDaily, b: IngredientUsageDaily) => a.qty_used - b.qty_used,
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
          <Select
            placeholder="Ингредиент"
            allowClear
            style={{ width: 200 }}
            value={selectedIngredientCode}
            onChange={setSelectedIngredientCode}
          >
            {ingredients.map(ing => (
              <Select.Option key={ing.code || ing.ingredient_code} value={ing.code || ing.ingredient_code}>
                {ing.name_ru || ing.display_name_ru || ing.name || ing.code || ing.ingredient_code}
              </Select.Option>
            ))}
          </Select>
        </Space>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : usage.length > 0 ? (
          <>
            {chartDataArray.length > 0 && (
              <div style={{ marginBottom: 24, height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartDataArray}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {uniqueIngredients.map((ingName, index) => (
                      <Line
                        key={ingName}
                        type="monotone"
                        dataKey={ingName}
                        stroke={`hsl(${(index * 360) / uniqueIngredients.length}, 70%, 50%)`}
                        strokeWidth={2}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            <Table
              dataSource={usage}
              columns={columns}
              rowKey={(record, index) => `${record.day}-${record.ingredient_code}-${index}`}
              pagination={{ pageSize: 50 }}
            />
          </>
        ) : (
          <Empty description="Нет данных о расходе за выбранный период" />
        )}
      </Card>
    </div>
  );
};

export default UsageDailyTab;
