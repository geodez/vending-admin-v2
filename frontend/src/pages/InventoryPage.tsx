import { useState } from 'react';
import { Typography, Tabs } from 'antd';
import StockBalanceTab from '../components/inventory/StockBalanceTab';
import LoadsHistoryTab from '../components/inventory/LoadsHistoryTab';
import UsageDailyTab from '../components/inventory/UsageDailyTab';
import VariableExpensesTab from '../components/inventory/VariableExpensesTab';

const { Title, Text } = Typography;

const InventoryPage = () => {
  const [activeTab, setActiveTab] = useState('balance');

  const tabItems = [
    {
      key: 'balance',
      label: 'Остатки',
      children: <StockBalanceTab />,
    },
    {
      key: 'loads',
      label: 'Загрузки (История)',
      children: <LoadsHistoryTab />,
    },
    {
      key: 'usage',
      label: 'Расход по дням',
      children: <UsageDailyTab />,
    },
    {
      key: 'expenses',
      label: 'Переменные расходы',
      children: <VariableExpensesTab />,
    },
  ];

  return (
    <div>
      <Title level={2}>📦 Склад</Title>
      <Text type="secondary">Управление складом и ингредиентами</Text>
      
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ marginTop: 16 }}
      />
    </div>
  );
};

export default InventoryPage;
