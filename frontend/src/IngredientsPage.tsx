import { useEffect, useState, useMemo } from 'react';
import { Card, Typography, Table, Button, Empty, message, Modal, Form, Input, InputNumber, Select, Space, Popconfirm, Tag, Switch, Checkbox, Row, Col, Dropdown, Badge } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined, SearchOutlined, CheckSquareOutlined } from '@ant-design/icons';
import { getIngredients, createIngredient, updateIngredient, deleteIngredient, bulkUpdateIngredients } from '../api/business';
import type { Ingredient } from '@/types/api';

const { Title, Text } = Typography;

interface IngredientFormData {
  ingredient_code: string;
  display_name_ru?: string;
  ingredient_group?: string;
  brand_name?: string;
  unit: string;
  unit_ru?: string;
  cost_per_unit_rub?: number;
  default_load_qty?: number;
  alert_threshold?: number;
  alert_days_threshold?: number;
  sort_order?: number;
  expense_kind: string;
  is_active: boolean;
}

const IngredientsPage = () => {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingIngredient, setEditingIngredient] = useState<Ingredient | null>(null);
  const [form] = Form.useForm();
  
  // Фильтры
  const [searchText, setSearchText] = useState('');
  const [filterGroup, setFilterGroup] = useState<string | undefined>(undefined);
  const [filterBrand, setFilterBrand] = useState<string | undefined>(undefined);
  const [filterExpenseKind, setFilterExpenseKind] = useState<string | undefined>(undefined);
  const [filterIsActive, setFilterIsActive] = useState<boolean | undefined>(undefined);
  
  // Видимость колонок
  const [visibleColumns, setVisibleColumns] = useState<Record<string, boolean>>({
    ingredient_code: true,
    display_name_ru: true,
    ingredient_group: true,
    brand_name: true,
    unit: true,
    cost_per_unit_rub: true,
    expense_kind: true,
    is_active: true,
    actions: true,
  });
  
  // Выбранные ингредиенты для массового редактирования
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [bulkEditModalVisible, setBulkEditModalVisible] = useState(false);
  const [bulkEditForm] = Form.useForm();

  const fetchIngredients = async () => {
    setLoading(true);
    try {
      const response = await getIngredients();
      // API возвращает массив напрямую, не в data
      setIngredients(Array.isArray(response.data) ? response.data : []);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки ингредиентов');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIngredients();
  }, []);

  const handleCreate = () => {
    setEditingIngredient(null);
    form.resetFields();
    form.setFieldsValue({
      expense_kind: 'stock_tracked',
      is_active: true,
      alert_days_threshold: 3,
      sort_order: 0,
    });
    setModalVisible(true);
  };

  const handleEdit = (ingredient: any) => {
    setEditingIngredient(ingredient);
    const code = ingredient.ingredient_code || ingredient.code;
    form.setFieldsValue({
      ingredient_code: code,
      display_name_ru: ingredient.display_name_ru || ingredient.name_ru || ingredient.name,
      ingredient_group: ingredient.ingredient_group,
      brand_name: ingredient.brand_name,
      unit: ingredient.unit,
      unit_ru: ingredient.unit_ru,
      cost_per_unit_rub: ingredient.cost_per_unit_rub || ingredient.unit_cost_rub ? Number(ingredient.cost_per_unit_rub || ingredient.unit_cost_rub) : undefined,
      default_load_qty: ingredient.default_load_qty || ingredient.pkg_qty ? Number(ingredient.default_load_qty || ingredient.pkg_qty) : undefined,
      alert_threshold: ingredient.alert_threshold || ingredient.alert_threshold_qty ? Number(ingredient.alert_threshold || ingredient.alert_threshold_qty) : undefined,
      alert_days_threshold: ingredient.alert_days_threshold || ingredient.alert_threshold_days,
      sort_order: ingredient.sort_order,
      expense_kind: ingredient.expense_kind || 'stock_tracked',
      is_active: ingredient.is_active !== undefined ? ingredient.is_active : true,
    });
    setModalVisible(true);
  };

  const handleDelete = async (code: string) => {
    try {
      await deleteIngredient(code);
      message.success('Ингредиент удален');
      fetchIngredients();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при удалении');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data: IngredientFormData = {
        ...values,
        cost_per_unit_rub: values.cost_per_unit_rub || undefined,
        default_load_qty: values.default_load_qty || undefined,
        alert_threshold: values.alert_threshold || undefined,
      };

      if (editingIngredient) {
        const code = (editingIngredient as any).ingredient_code || (editingIngredient as any).code;
        await updateIngredient(code, data as any);
        message.success('Ингредиент обновлен');
      } else {
        await createIngredient(data as any);
        message.success('Ингредиент создан');
      }
      setModalVisible(false);
      fetchIngredients();
    } catch (error: any) {
      if (error.errorFields) {
        return; // Form validation errors
      }
      message.error(error.response?.data?.detail || 'Ошибка при сохранении');
    }
  };

  // Получаем уникальные значения для фильтров
  const uniqueGroups = useMemo(() => {
    const groups = new Set<string>();
    ingredients.forEach(ing => {
      const group = (ing as any).ingredient_group;
      if (group) groups.add(group);
    });
    return Array.from(groups).sort();
  }, [ingredients]);

  const uniqueBrands = useMemo(() => {
    const brands = new Set<string>();
    ingredients.forEach(ing => {
      const brand = (ing as any).brand_name;
      if (brand) brands.add(brand);
    });
    return Array.from(brands).sort();
  }, [ingredients]);

  // Фильтрация данных
  const filteredIngredients = useMemo(() => {
    return ingredients.filter((ing: any) => {
      // Поиск по тексту (код, название)
      if (searchText) {
        const searchLower = searchText.toLowerCase();
        const code = (ing.ingredient_code || ing.code || '').toLowerCase();
        const name = (ing.display_name_ru || ing.name_ru || ing.name || '').toLowerCase();
        if (!code.includes(searchLower) && !name.includes(searchLower)) {
          return false;
        }
      }

      // Фильтр по группе
      if (filterGroup && (ing.ingredient_group || '') !== filterGroup) {
        return false;
      }

      // Фильтр по бренду
      if (filterBrand && (ing.brand_name || '') !== filterBrand) {
        return false;
      }

      // Фильтр по типу учета
      if (filterExpenseKind && (ing.expense_kind || '') !== filterExpenseKind) {
        return false;
      }

      // Фильтр по статусу
      if (filterIsActive !== undefined && ing.is_active !== filterIsActive) {
        return false;
      }

      return true;
    });
  }, [ingredients, searchText, filterGroup, filterBrand, filterExpenseKind, filterIsActive]);

  // Обработка изменения видимости колонок
  const handleColumnVisibilityChange = (key: string, visible: boolean) => {
    setVisibleColumns(prev => ({ ...prev, [key]: visible }));
  };

  // Меню для настройки колонок
  const columnSettingsMenu = {
    items: [
      { key: 'ingredient_code', label: 'Код' },
      { key: 'display_name_ru', label: 'Название' },
      { key: 'ingredient_group', label: 'Группа' },
      { key: 'brand_name', label: 'Бренд' },
      { key: 'unit', label: 'Единица' },
      { key: 'cost_per_unit_rub', label: 'Цена за единицу' },
      { key: 'expense_kind', label: 'Тип' },
      { key: 'is_active', label: 'Статус' },
    ].map(item => ({
      key: item.key,
      label: (
        <Checkbox
          checked={visibleColumns[item.key]}
          onChange={(e) => handleColumnVisibilityChange(item.key, e.target.checked)}
        >
          {item.label}
        </Checkbox>
      ),
    })),
  };

  // Обработка массового редактирования
  const handleBulkEdit = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите ингредиенты для редактирования');
      return;
    }
    bulkEditForm.resetFields();
    setBulkEditModalVisible(true);
  };

  const handleBulkEditSubmit = async () => {
    try {
      const values = await bulkEditForm.validateFields();
      const codes = selectedRowKeys.map(key => String(key));
      
      // Подготавливаем данные для обновления (только измененные поля)
      const updateData: any = {};
      if (values.expense_kind !== undefined) {
        updateData.expense_kind = values.expense_kind;
      }
      if (values.is_active !== undefined) {
        updateData.is_active = values.is_active;
      }
      
      if (Object.keys(updateData).length === 0) {
        message.warning('Выберите параметры для изменения');
        return;
      }

      const result = await bulkUpdateIngredients(codes, updateData);
      
      if (result.data.errors && result.data.errors.length > 0) {
        message.warning(`Обновлено ${result.data.updated} из ${result.data.total}. Ошибки: ${result.data.errors.join(', ')}`);
      } else {
        message.success(`Успешно обновлено ${result.data.updated} ингредиентов`);
      }
      
      setBulkEditModalVisible(false);
      setSelectedRowKeys([]);
      fetchIngredients();
    } catch (error: any) {
      if (error.errorFields) {
        return; // Form validation errors
      }
      message.error(error.response?.data?.detail || 'Ошибка при массовом обновлении');
    }
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (selectedKeys: React.Key[]) => {
      setSelectedRowKeys(selectedKeys);
    },
    onSelectAll: (selected: boolean, selectedRows: any[], changeRows: any[]) => {
      if (selected) {
        const allKeys = filteredIngredients.map((ing: any) => ing.ingredient_code || ing.code || '');
        setSelectedRowKeys(allKeys);
      } else {
        setSelectedRowKeys([]);
      }
    },
  };

  const allColumns = [
    {
      title: 'Код',
      dataIndex: 'ingredient_code',
      key: 'ingredient_code',
      width: 150,
      render: (_: any, record: any) => record.ingredient_code || record.code || '-',
      sorter: (a: any, b: any) => (a.ingredient_code || a.code || '').localeCompare(b.ingredient_code || b.code || ''),
    },
    {
      title: 'Название',
      dataIndex: 'display_name_ru',
      key: 'display_name_ru',
      render: (text: string | null) => text || '-',
    },
    {
      title: 'Группа',
      dataIndex: 'ingredient_group',
      key: 'ingredient_group',
      render: (text: string | null) => text || '-',
    },
    {
      title: 'Бренд',
      dataIndex: 'brand_name',
      key: 'brand_name',
      render: (text: string | null) => text || '-',
    },
    {
      title: 'Единица',
      dataIndex: 'unit',
      key: 'unit',
      width: 100,
      render: (unit: string, record: any) => record.unit_ru || record.unit || unit,
    },
    {
      title: 'Цена за единицу',
      dataIndex: 'cost_per_unit_rub',
      key: 'cost_per_unit_rub',
      width: 130,
      render: (value: number | null, record: any) => {
        const cost = value || record.unit_cost_rub;
        return cost ? `${Number(cost).toFixed(2)} ₽` : '-';
      },
      sorter: (a: any, b: any) => (a.cost_per_unit_rub || a.unit_cost_rub || 0) - (b.cost_per_unit_rub || b.unit_cost_rub || 0),
    },
    {
      title: 'Тип',
      dataIndex: 'expense_kind',
      key: 'expense_kind',
      width: 120,
      render: (kind: string) => (
        <Tag color={kind === 'stock_tracked' ? 'blue' : 'default'}>
          {kind === 'stock_tracked' ? 'Учитывается' : 'Не учитывается'}
        </Tag>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Активен' : 'Неактивен'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить ингредиент?"
            onConfirm={() => handleDelete(record.ingredient_code || record.code)}
            okText="Да"
            cancelText="Нет"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Фильтруем колонки по видимости
  const columns = allColumns.filter(col => visibleColumns[col.key] !== false);

  return (
    <div>
      <Title level={2}>🛒 Ингредиенты</Title>
      <Text type="secondary">Управление ингредиентами для рецептов</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Добавить ингредиент
            </Button>
            {selectedRowKeys.length > 0 && (
              <Badge count={selectedRowKeys.length} showZero>
                <Button
                  icon={<CheckSquareOutlined />}
                  onClick={handleBulkEdit}
                >
                  Массовое редактирование ({selectedRowKeys.length})
                </Button>
              </Badge>
            )}
          </Space>
          <Dropdown menu={columnSettingsMenu} trigger={['click']}>
            <Button icon={<SettingOutlined />}>
              Настройка колонок
            </Button>
          </Dropdown>
        </div>

        {/* Панель фильтров */}
        <Card size="small" style={{ marginBottom: 16, background: '#fafafa' }}>
          <Row gutter={[16, 8]}>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Input
                placeholder="Поиск по коду или названию..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Select
                placeholder="Группа"
                style={{ width: '100%' }}
                value={filterGroup}
                onChange={setFilterGroup}
                allowClear
              >
                {uniqueGroups.map(group => (
                  <Select.Option key={group} value={group}>{group}</Select.Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Select
                placeholder="Бренд"
                style={{ width: '100%' }}
                value={filterBrand}
                onChange={setFilterBrand}
                allowClear
              >
                {uniqueBrands.map(brand => (
                  <Select.Option key={brand} value={brand}>{brand}</Select.Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Select
                placeholder="Тип учета"
                style={{ width: '100%' }}
                value={filterExpenseKind}
                onChange={setFilterExpenseKind}
                allowClear
              >
                <Select.Option value="stock_tracked">Учитывается</Select.Option>
                <Select.Option value="not_tracked">Не учитывается</Select.Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Select
                placeholder="Статус"
                style={{ width: '100%' }}
                value={filterIsActive === undefined ? undefined : filterIsActive ? 'active' : 'inactive'}
                onChange={(value) => setFilterIsActive(value === undefined ? undefined : value === 'active')}
                allowClear
              >
                <Select.Option value="active">Активен</Select.Option>
                <Select.Option value="inactive">Неактивен</Select.Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8} lg={6}>
              <Button
                onClick={() => {
                  setSearchText('');
                  setFilterGroup(undefined);
                  setFilterBrand(undefined);
                  setFilterExpenseKind(undefined);
                  setFilterIsActive(undefined);
                }}
                style={{ width: '100%' }}
              >
                Сбросить фильтры
              </Button>
            </Col>
          </Row>
          {(searchText || filterGroup || filterBrand || filterExpenseKind !== undefined || filterIsActive !== undefined) && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              Найдено: {filteredIngredients.length} из {ingredients.length}
            </div>
          )}
        </Card>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Text>Загрузка...</Text>
          </div>
        ) : filteredIngredients.length > 0 ? (
          <Table
            dataSource={filteredIngredients}
            columns={columns}
            rowKey={(record: any) => record.ingredient_code || record.code || ''}
            rowSelection={rowSelection}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
            scroll={{ x: 'max-content' }}
          />
        ) : ingredients.length > 0 ? (
          <Empty description="Нет ингредиентов, соответствующих фильтрам." />
        ) : (
          <Empty description="Нет ингредиентов. Добавьте первый ингредиент." />
        )}
      </Card>

      <Modal
        title={editingIngredient ? 'Редактировать ингредиент' : 'Добавить ингредиент'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            expense_kind: 'stock_tracked',
            is_active: true,
            alert_days_threshold: 3,
            sort_order: 0,
          }}
        >
          <Form.Item
            name="ingredient_code"
            label="Код ингредиента"
            rules={[{ required: true, message: 'Введите код ингредиента' }]}
          >
            <Input disabled={!!editingIngredient} placeholder="Например: COFFEE_BEANS" />
          </Form.Item>

          <Form.Item
            name="display_name_ru"
            label="Название (RU)"
          >
            <Input placeholder="Например: Кофе в зернах" />
          </Form.Item>

          <Form.Item
            name="ingredient_group"
            label="Группа"
          >
            <Input placeholder="Например: Coffee, Milk, Syrups" />
          </Form.Item>

          <Form.Item
            name="brand_name"
            label="Бренд"
          >
            <Input placeholder="Название бренда" />
          </Form.Item>

          <Form.Item
            name="unit"
            label="Единица измерения"
            rules={[{ required: true, message: 'Введите единицу измерения' }]}
          >
            <Input placeholder="g, ml, pcs" />
          </Form.Item>

          <Form.Item
            name="unit_ru"
            label="Единица измерения (RU)"
          >
            <Input placeholder="г, мл, шт" />
          </Form.Item>

          <Form.Item
            name="cost_per_unit_rub"
            label="Цена за единицу (руб)"
          >
            <InputNumber
              min={0}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="0.00"
            />
          </Form.Item>

          <Form.Item
            name="default_load_qty"
            label="Количество по умолчанию при загрузке"
          >
            <InputNumber
              min={0}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="0.00"
            />
          </Form.Item>

          <Form.Item
            name="alert_threshold"
            label="Порог предупреждения (минимальный остаток)"
          >
            <InputNumber
              min={0}
              step={0.01}
              style={{ width: '100%' }}
              placeholder="0.00"
            />
          </Form.Item>

          <Form.Item
            name="alert_days_threshold"
            label="Порог предупреждения (дней)"
          >
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              placeholder="3"
            />
          </Form.Item>

          <Form.Item
            name="sort_order"
            label="Порядок сортировки"
          >
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              placeholder="0"
            />
          </Form.Item>

          <Form.Item
            name="expense_kind"
            label="Тип учета"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="stock_tracked">Учитывается на складе</Select.Option>
              <Select.Option value="not_tracked">Не учитывается</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Активен"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно массового редактирования */}
      <Modal
        title={`Массовое редактирование (${selectedRowKeys.length} ингредиентов)`}
        open={bulkEditModalVisible}
        onOk={handleBulkEditSubmit}
        onCancel={() => setBulkEditModalVisible(false)}
        width={500}
        okText="Применить"
        cancelText="Отмена"
      >
        <Form
          form={bulkEditForm}
          layout="vertical"
        >
          <Form.Item
            name="expense_kind"
            label="Тип учета"
            tooltip="Оставьте пустым, чтобы не изменять"
          >
            <Select placeholder="Не изменять" allowClear>
              <Select.Option value="stock_tracked">Учитывается на складе</Select.Option>
              <Select.Option value="not_tracked">Не учитывается</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Статус"
            tooltip="Оставьте пустым, чтобы не изменять"
          >
            <Select placeholder="Не изменять" allowClear>
              <Select.Option value={true}>Активен</Select.Option>
              <Select.Option value={false}>Неактивен</Select.Option>
            </Select>
          </Form.Item>

          <div style={{ marginTop: 16, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Изменения будут применены ко всем выбранным ингредиентам. 
              Поля, оставленные пустыми, не будут изменены.
            </Text>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default IngredientsPage;
