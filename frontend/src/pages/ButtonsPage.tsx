import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const ButtonsPage = () => {
  return (
    <div>
      <Title level={2}>Buttons</Title>
      <Text type="secondary">Страница Buttons</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default ButtonsPage;
