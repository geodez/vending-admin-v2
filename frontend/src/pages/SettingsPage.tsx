import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const SettingsPage = () => {
  return (
    <div>
      <Title level={2}>Settings</Title>
      <Text type="secondary">Страница Settings</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default SettingsPage;
