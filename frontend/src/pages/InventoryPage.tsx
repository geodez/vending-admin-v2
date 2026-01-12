import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const InventoryPage = () => {
  return (
    <div>
      <Title level={2}>Inventory</Title>
      <Text type="secondary">Страница Inventory</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default InventoryPage;
