import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const ExpensesPage = () => {
  return (
    <div>
      <Title level={2}>Expenses</Title>
      <Text type="secondary">Страница Expenses</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default ExpensesPage;
