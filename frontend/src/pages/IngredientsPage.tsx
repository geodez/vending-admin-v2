import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const IngredientsPage = () => {
  return (
    <div>
      <Title level={2}>Ingredients</Title>
      <Text type="secondary">Страница Ingredients</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default IngredientsPage;
