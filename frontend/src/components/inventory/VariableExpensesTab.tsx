import { useEffect, useState } from 'react';
import { Card, Table, Button, Select, DatePicker, Space, Empty, Spin, message, Modal, Form, Input, InputNumber } from 'antd';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { expensesApi, Expense, ExpenseCreate } from '../../api/expenses';
import { getTerminals, VendistaTerminal } from '../../api/sync';
import { getLocations } from '../../api/business';
import { EXPENSE_CATEGORIES } from '../../utils/constants';
import type { Location } from '@/types/api';
import dayjs, { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

const VariableExpensesTab = () => {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form] = Form.useForm();
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().startOf('month'),
    dayjs(),
  ]);
  const [terminals, setTerminals] = useState<VendistaTerminal[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [terminalsLoading, setTerminalsLoading] = useState(false);
  const [categories, setCategories] = useState<string[]>([...EXPENSE_CATEGORIES]);
  const [newCategoryInput, setNewCategoryInput] = useState('');
  const [showNewCategoryInput, setShowNewCategoryInput] = useState(false);

  useEffect(() => {
    fetchExpenses();
    fetchTerminals();
    fetchLocations();
  }, []);

  useEffect(() => {
    fetchExpenses();
  }, [dateRange]);

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

  const fetchTerminals = async () => {
    setTerminalsLoading(true);
    try {
      const response = await getTerminals();
      setTerminals(response.data);
    } catch (error: any) {
      if (error.response?.status !== 404) {
        console.error('Error fetching terminals:', error);
      }
    } finally {
      setTerminalsLoading(false);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await getLocations();
      setLocations(Array.isArray(response.data) ? response.data : []);
    } catch (error: any) {
      console.error('Ошибка загрузки локаций:', error);
    }
  };

  const handleCreate = () => {
    setEditingId(null);
    form.resetFields();
    form.setFieldsValue({ expense_date: dayjs() });
    setShowNewCategoryInput(false);
    setNewCategoryInput('');
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

  const handleAddCategory = () => {
    if (newCategoryInput.trim() && !categories.includes(newCategoryInput.trim())) {
      setCategories([...categories, newCategoryInput.trim()]);
      setNewCategoryInput('');
      setShowNewCategoryInput(false);
      message.success('Категория добавлена');
    } else if (categories.includes(newCategoryInput.trim())) {
      message.warning('Такая категория уже существует');
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

  // Расчет сводки по категориям
  const categorySummary = expenses.reduce((acc, expense) => {
    const cat = expense.category || 'Прочее';
    if (!acc[cat]) {
      acc[cat] = 0;
    }
    acc[cat] += expense.amount_rub;
    return acc;
  }, {} as Record<string, number>);

  const totalAmount = Object.values(categorySummary).reduce((sum, val) => sum + val, 0);

  // Данные для pie chart
  const pieData = Object.entries(categorySummary).map(([name, value]) => ({
    name,
    value: Number(value.toFixed(2)),
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

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
      render: (locationId: number | null) => {
        if (locationId === null) return '-';
        const loc = locations.find(l => l.id === locationId);
        return loc?.name || `ID: ${locationId}`;
      },
    },
    {
      title: 'Терминал',
      dataIndex: 'vendista_term_id',
      key: 'vendista_term_id',
      render: (vendistaTermId: number | null) => {
        if (vendistaTermId === null || vendistaTermId === undefined) {
          return '-';
        }
        const terminal = terminals.find(t => t.id === vendistaTermId);
        if (terminal) {
          return `${terminal.comment || terminal.title || 'Терминал'} (ID: ${vendistaTermId})`;
        }
        return `ID: ${vendistaTermId}`;
      },
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
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16, flexWrap: 'wrap' }}>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="DD.MM.YYYY"
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Добавить расход
          </Button>
        </Space>

        {/* Сводка по категориям */}
        {Object.keys(categorySummary).length > 0 && (
          <Card style={{ marginBottom: 16 }}>
            <h3>💰 Сводка переменных расходов за период</h3>
            <Space direction="vertical" style={{ width: '100%' }}>
              {Object.entries(categorySummary).map(([category, amount]) => (
                <div key={category} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0' }}>
                  <span>{category}</span>
                  <strong>{amount.toFixed(2)} ₽</strong>
                </div>
              ))}
              <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 8, marginTop: 8, display: 'flex', justifyContent: 'space-between' }}>
                <strong>ИТОГО</strong>
                <strong>{totalAmount.toFixed(2)} ₽</strong>
              </div>
            </Space>

            {/* Pie Chart */}
            {pieData.length > 0 && (
              <div style={{ marginTop: 24, height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        )}

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
        onCancel={() => {
          setModalOpen(false);
          setShowNewCategoryInput(false);
          setNewCategoryInput('');
        }}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="expense_date" label="Дата" rules={[{ required: true }]}>
            <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="vendista_term_id" label="Терминал" rules={[{ required: true, message: 'Выберите терминал' }]}>
            <Select
              placeholder="Выберите терминал"
              loading={terminalsLoading}
              showSearch
              allowClear
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={terminals.map(term => ({
                value: term.id,
                label: `${term.comment || term.title || `Терминал #${term.id}`} (ID: ${term.id})`
              }))}
            />
          </Form.Item>
          <Form.Item name="category" label="Категория" rules={[{ required: true, message: 'Выберите категорию' }]}>
            <Select
              placeholder="Выберите категорию"
              showSearch
              allowClear
              dropdownRender={(menu) => (
                <>
                  {menu}
                  <div style={{ padding: '8px', borderTop: '1px solid #f0f0f0' }}>
                    {showNewCategoryInput ? (
                      <Space.Compact style={{ width: '100%' }}>
                        <Input
                          placeholder="Новая категория"
                          value={newCategoryInput}
                          onChange={(e) => setNewCategoryInput(e.target.value)}
                          onPressEnter={handleAddCategory}
                          autoFocus
                        />
                        <Button type="primary" onClick={handleAddCategory}>
                          Добавить
                        </Button>
                        <Button onClick={() => {
                          setShowNewCategoryInput(false);
                          setNewCategoryInput('');
                        }}>
                          Отмена
                        </Button>
                      </Space.Compact>
                    ) : (
                      <Button
                        type="link"
                        icon={<PlusOutlined />}
                        onClick={() => setShowNewCategoryInput(true)}
                        style={{ width: '100%' }}
                      >
                        Добавить новую категорию
                      </Button>
                    )}
                  </div>
                </>
              )}
            >
              {categories.map(cat => (
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

export default VariableExpensesTab;
