import { Card, Typography, Empty } from 'antd';

const { Title, Text } = Typography;

const OwnerReportPage = () => {
  return (
    <div>
      <Title level={2}>OwnerReport</Title>
      <Text type="secondary">Страница OwnerReport</Text>
      <Card style={{ marginTop: 16 }}>
        <Empty description="Страница в разработке. Будет доступна после API интеграции." />
      </Card>
    </div>
  );
};

export default OwnerReportPage;
