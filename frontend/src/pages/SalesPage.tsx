import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const SalesPage = () => {
  return (
    <div>
      <Title level={2}>📊 Продажи</Title>
      <Text type="secondary">Аналитика продаж по напиткам</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default SalesPage;
