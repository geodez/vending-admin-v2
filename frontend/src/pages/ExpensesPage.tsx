import { useEffect, useState } from 'react';
import { Card, Typography, Table, DatePicker, Button, Empty, message, Spin, Modal, Form, Input, InputNumber, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SyncOutlined } from '@ant-design/icons';
import { expensesApi, Expense, ExpenseCreate } from '../api/expenses';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const CATEGORIES = ['ingredients', 'rent', 'launch', 'utilities', 'maintenance', 'other'];

const ExpensesPage = () => {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm();
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs()
  ]);

  const fetchExpenses = async () => {
    setLoading(true);
    try {
      const data = await expensesApi.getExpenses({
        period_start: dateRange[0].format('YYYY-MM-DD'),
        period_end: dateRange[1].format('YYYY-MM-DD'),
      });
      setExpenses(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки расходов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, []);

  const handleCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ expense_date: dayjs() });
    setModalOpen(true);
  };

  const handleEdit = (expense: Expense) => {
    setEditingId(expense.id);
    form.setFieldsValue({
      ...expense,
      expense_date: dayjs(expense.expense_date),
    });
    setModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await expensesApi.deleteExpense(id);
      message.success('Расход удален');
      fetchExpenses();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data: ExpenseCreate = {
        ...values,
        expense_date: values.expense_date.format('YYYY-MM-DD'),
      };

      if (editingId) {
        await expensesApi.updateExpense(editingId, data);
        message.success('Расход обновлен');
      } else {
        await expensesApi.createExpense(data);
        message.success('Расход создан');
      }

      setModalOpen(false);
      fetchExpenses();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const columns = [
    {
      title: 'Дата',
      dataIndex: 'expense_date',
      key: 'expense_date',
      render: (value: string) => dayjs(value).format('DD.MM.YYYY'),
      sorter: (a: Expense, b: Expense) => a.expense_date.localeCompare(b.expense_date),
    },
    {
      title: 'Локация',
      dataIndex: 'location_id',
      key: 'location_id',
    },
    {
      title: 'Категория',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: 'Сумма',
      dataIndex: 'amount_rub',
      key: 'amount_rub',
      render: (value: number) => `${value.toFixed(2)} ₽`,
      sorter: (a: Expense, b: Expense) => a.amount_rub - b.amount_rub,
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: Expense) => (
        <div style={{ display: 'flex', gap: 8 }}>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
        </div>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>💰 Расходы</Title>
      <Text type="secondary">Учет переменных расходов</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
          />
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={fetchExpenses}
            loading={loading}
          >
            Обновить
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Добавить расход
          </Button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : expenses.length > 0 ? (
          <Table
            dataSource={expenses}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 20 }}
          />
        ) : (
          <Empty description="Нет расходов за выбранный период." />
        )}
      </Card>

      <Modal
        title={editingId ? 'Редактировать расход' : 'Добавить расход'}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="expense_date" label="Дата" rules={[{ required: true }]}>
            <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="location_id" label="ID Локации" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="category" label="Категория" rules={[{ required: true }]}>
            <Select>
              {CATEGORIES.map(cat => (
                <Select.Option key={cat} value={cat}>{cat}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="amount_rub" label="Сумма (руб)" rules={[{ required: true }]}>
            <InputNumber min={0.01} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="comment" label="Комментарий">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ExpensesPage;
