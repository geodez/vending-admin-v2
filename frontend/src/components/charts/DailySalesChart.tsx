import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Card, Empty } from 'antd';
import dayjs from 'dayjs';
import { formatCurrency } from '@/utils/formatters';

interface DailySalesData {
  date: string;
  revenue: number;
  net_profit: number;
  sales_count: number;
}

interface DailySalesChartProps {
  data: DailySalesData[];
  loading?: boolean;
}

const DailySalesChart: React.FC<DailySalesChartProps> = ({ data, loading }) => {
  if (!loading && (!data || data.length === 0)) {
    return (
      <Card title="📈 Динамика продаж" style={{ marginTop: 16 }}>
        <Empty description="Нет данных за выбранный период" />
      </Card>
    );
  }

  // Format dates for display
  const chartData = data.map(item => ({
    ...item,
    displayDate: dayjs(item.date).format('DD.MM'),
  }));

  return (
    <Card title="📈 Динамика продаж" style={{ marginTop: 16 }} loading={loading}>
      <div style={{ height: 400, width: '100%' }}>
        <ResponsiveContainer>
          <ComposedChart
            data={chartData}
            margin={{
              top: 20,
              right: 20,
              bottom: 20,
              left: 20,
            }}
          >
            <CartesianGrid stroke="#f5f5f5" />
            <XAxis dataKey="displayDate" scale="point" padding={{ left: 10, right: 10 }} />
            <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
            <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
            <Tooltip
              formatter={(value: number, name: string) => {
                if (name === 'revenue') return [formatCurrency(value), 'Выручка'];
                if (name === 'net_profit') return [formatCurrency(value), 'Чистая прибыль'];
                return [value, name];
              }}
              labelFormatter={(label) => `Дата: ${label}`}
            />
            <Legend />
            <Bar
              yAxisId="left"
              dataKey="revenue"
              name="Выручка"
              barSize={20}
              fill="#413ea0"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="net_profit"
              name="Чистая прибыль"
              stroke="#ff7300"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

export default DailySalesChart;
