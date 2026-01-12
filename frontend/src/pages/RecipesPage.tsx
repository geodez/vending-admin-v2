import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const RecipesPage = () => {
  return (
    <div>
      <Title level={2}>Recipes</Title>
      <Text type="secondary">Страница Recipes</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default RecipesPage;
