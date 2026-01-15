import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Empty, message, Spin, Modal, Form, Input, InputNumber, Switch } from 'antd';
import { PlusOutlined, SyncOutlined } from '@ant-design/icons';
import { mappingApi, Drink, DrinkCreate } from '../api/mapping';

const { Title, Text } = Typography;

const RecipesPage = () => {
  const [drinks, setDrinks] = useState<Drink[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();

  const fetchDrinks = async () => {
    setLoading(true);
    try {
      const data = await mappingApi.getDrinks();
      setDrinks(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки напитков');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDrinks();
  }, []);

  const handleCreate = () => {
    form.resetFields();
    form.setFieldsValue({ is_active: true });
    setModalOpen(true);
  };

  const handleSubmit = async (values: DrinkCreate) => {
    try {
      await mappingApi.createDrink(values);
      message.success('Напиток добавлен');
      setModalOpen(false);
      fetchDrinks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка создания');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Цена закупки',
      dataIndex: 'purchase_price_rub',
      key: 'purchase_price_rub',
      render: (value: number | null) => value !== null ? `${value.toFixed(2)} ₽` : '-',
    },
    {
      title: 'Цена продажи',
      dataIndex: 'sale_price_rub',
      key: 'sale_price_rub',
      render: (value: number | null) => value !== null ? `${value.toFixed(2)} ₽` : '-',
    },
    {
      title: 'Активен',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => value ? '✓' : '✗',
    },
  ];

  return (
    <div>
      <Title level={2}>☕ Рецепты / Напитки</Title>
      <Text type="secondary">Справочник напитков и рецептов</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={fetchDrinks}
            loading={loading}
          >
            Обновить
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Добавить напиток
          </Button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : drinks.length > 0 ? (
          <Table
            dataSource={drinks}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 20 }}
          />
        ) : (
          <Empty description="Нет напитков. Добавьте справочник напитков для корректной работы KPI views." />
        )}
      </Card>

      <Modal
        title="Добавить напиток"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="purchase_price_rub" label="Цена закупки (руб)">
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="sale_price_rub" label="Цена продажи (руб)">
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="is_active" label="Активен" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RecipesPage;
