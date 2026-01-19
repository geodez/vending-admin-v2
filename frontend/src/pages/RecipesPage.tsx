import { useEffect, useState, useMemo } from 'react';
import { Card, Typography, Table, Button, Empty, message, Modal, Form, Input, InputNumber, Select, Space, Popconfirm, Tag, Switch, Checkbox, Badge, Tooltip } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckSquareOutlined, SearchOutlined, DollarOutlined } from '@ant-design/icons';
import { mappingApi, Drink, DrinkCreate, DrinkUpdate, DrinkItem } from '../api/mapping';
import { getIngredients } from '../api/business';
import type { Ingredient } from '@/types/api';

const { Title, Text } = Typography;

const RecipesPage = () => {
  const [drinks, setDrinks] = useState<Drink[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [bulkEditModalOpen, setBulkEditModalOpen] = useState(false);
  const [editingDrink, setEditingDrink] = useState<Drink | null>(null);
  const [form] = Form.useForm();
  const [bulkEditForm] = Form.useForm();
  
  // Фильтры
  const [searchText, setSearchText] = useState('');
  const [filterIsActive, setFilterIsActive] = useState<boolean | undefined>(undefined);
  const [groupBy, setGroupBy] = useState<'none' | 'base_name' | 'volume'>('none');
  
  // Выбранные рецепты для массового редактирования
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

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

  const fetchIngredients = async () => {
    try {
      const data = await getIngredients();
      setIngredients(data.data || data);
    } catch (error: any) {
      console.error('Ошибка загрузки ингредиентов:', error);
    }
  };

  useEffect(() => {
    fetchDrinks();
    fetchIngredients();
  }, []);

  // Извлечение базового названия (без объема и вариантов типа Strong, Stronge и т.д.)
  const getBaseName = (name: string): string => {
    let baseName = name;
    
    // Удаляем объем (250 мл, 350 мл, 120 мл и т.д.)
    baseName = baseName.replace(/\s+\d+\s*мл\.?/i, '').trim();
    
    // Удаляем варианты напитков (Strong, Stronge, Двойной, и другие модификаторы)
    // Список модификаторов, которые нужно удалить
    const modifiers = [
      /\s+stronge?\s*/i,      // Strong, Stronge
      /\s+strong\s*/i,        // Strong
      /\s+light\s*/i,         // Light
      /\s+double\s*/i,        // Double
      /\s+single\s*/i,        // Single
      /^двойной\s+/i,         // Двойной в начале
      /\s+двойной\s+/i,       // Двойной в середине
      /\s+одинарный\s*/i,     // Одинарный
    ];
    
    for (const modifier of modifiers) {
      baseName = baseName.replace(modifier, ' ').trim();
    }
    
    // Удаляем лишние пробелы
    baseName = baseName.replace(/\s+/g, ' ').trim();
    
    return baseName;
  };

  // Извлечение объема из названия
  const getVolume = (name: string): string | null => {
    const match = name.match(/(\d+)\s*мл\.?/i);
    return match ? match[1] + ' мл' : null;
  };

  // Фильтрация и группировка рецептов
  const { filteredDrinks, groupedDrinks } = useMemo(() => {
    // Сначала фильтруем
    const filtered = drinks.filter((drink) => {
      const matchesSearch = !searchText || 
        drink.name.toLowerCase().includes(searchText.toLowerCase());
      const matchesStatus = filterIsActive === undefined || drink.is_active === filterIsActive;
      return matchesSearch && matchesStatus;
    });

    // Затем группируем
    if (groupBy === 'none') {
      return { filteredDrinks: filtered, groupedDrinks: null };
    } else if (groupBy === 'base_name') {
      const grouped: Record<string, Drink[]> = {};
      filtered.forEach((drink) => {
        const baseName = getBaseName(drink.name);
        if (!grouped[baseName]) {
          grouped[baseName] = [];
        }
        grouped[baseName].push(drink);
      });
      return { filteredDrinks: filtered, groupedDrinks: grouped };
    } else if (groupBy === 'volume') {
      const grouped: Record<string, Drink[]> = {};
      filtered.forEach((drink) => {
        const volume = getVolume(drink.name) || 'Без объема';
        if (!grouped[volume]) {
          grouped[volume] = [];
        }
        grouped[volume].push(drink);
      });
      return { filteredDrinks: filtered, groupedDrinks: grouped };
    }

    return { filteredDrinks: filtered, groupedDrinks: null };
  }, [drinks, searchText, filterIsActive, groupBy]);

  const handleCreate = () => {
    form.resetFields();
    form.setFieldsValue({ is_active: true, items: [] });
    setEditingDrink(null);
    setModalOpen(true);
  };

  const handleEdit = (drink: Drink) => {
    form.resetFields();
    form.setFieldsValue({
      name: drink.name,
      is_active: drink.is_active,
      items: drink.items || []
    });
    setEditingDrink(drink);
    setModalOpen(true);
  };

  const handleDelete = async (drinkId: number) => {
    try {
      await mappingApi.deleteDrink(drinkId);
      message.success('Напиток удален');
      fetchDrinks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingDrink) {
        const drinkData: DrinkUpdate = {
          name: values.name,
          is_active: values.is_active,
          items: values.items || []
        };
        await mappingApi.updateDrink(editingDrink.id, drinkData);
        message.success('Напиток обновлен');
      } else {
        const drinkData: DrinkCreate = {
          name: values.name,
          is_active: values.is_active,
          items: values.items || []
        };
        await mappingApi.createDrink(drinkData);
        message.success('Напиток добавлен');
      }
      
      setModalOpen(false);
      fetchDrinks();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleBulkEdit = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите рецепты для редактирования');
      return;
    }
    bulkEditForm.resetFields();
    setBulkEditModalOpen(true);
  };

  const handleBulkEditSubmit = async () => {
    try {
      const values = await bulkEditForm.validateFields();
      
      const drinkIds = selectedRowKeys.map(key => Number(key));
      
      const updateData: any = {};
      if (values.is_active !== undefined) {
        updateData.is_active = values.is_active;
      }
      
      if (Object.keys(updateData).length === 0) {
        message.warning('Выберите параметры для изменения');
        return;
      }

      const result = await mappingApi.bulkUpdateDrinks(drinkIds, updateData);
      message.success(`Успешно обновлено ${result.updated} рецептов`);
      
      setBulkEditModalOpen(false);
      setSelectedRowKeys([]);
      fetchDrinks();
    } catch (error: any) {
      if (error.errorFields) {
        return; // Form validation errors
      }
      message.error(error.response?.data?.detail || 'Ошибка при массовом обновлении');
    }
  };

  const handleResetFilters = () => {
    setSearchText('');
    setFilterIsActive(undefined);
    setGroupBy('none');
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (selectedKeys: React.Key[]) => {
      setSelectedRowKeys(selectedKeys);
    },
    onSelectAll: (selected: boolean) => {
      if (selected) {
        const allKeys = filteredDrinks.map(drink => drink.id);
        setSelectedRowKeys(allKeys);
      } else {
        setSelectedRowKeys([]);
      }
    },
    getCheckboxProps: (record: Drink) => ({
      name: record.name,
    }),
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      fixed: 'left' as const,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      fixed: 'left' as const,
      render: (text: string) => text || '-',
    },
    {
      title: (
        <Tooltip title="Состав рецепта: список ингредиентов с их количеством на одну порцию">
          Состав
        </Tooltip>
      ),
      dataIndex: 'items',
      key: 'items',
      align: 'left' as const,
      ellipsis: true,
      render: (items: DrinkItem[] | undefined) => {
        if (!items || items.length === 0) {
          return <Text type="secondary" style={{ fontSize: '13px' }}>Нет ингредиентов</Text>;
        }
        
        return (
          <div style={{ width: '100%', padding: '4px 0' }}>
            {items.map((item, idx) => {
              // Используем display_name_ru из item, если есть, иначе ищем в списке ингредиентов
              const ingredientName = item.display_name_ru || (() => {
                const ingredient = ingredients.find(ing => {
                  const ingCode = ing.ingredient_code || ing.code;
                  return ingCode === item.ingredient_code;
                });
                return ingredient?.display_name_ru || item.ingredient_code;
              })();
              
              return (
                <div key={idx} style={{ fontSize: '12px', lineHeight: '1.6', marginBottom: 4, minHeight: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <Tag color="blue" style={{ margin: 0, fontSize: '11px', padding: '2px 6px', lineHeight: '1.4' }}>{ingredientName}</Tag>
                    <Text type="secondary" style={{ fontSize: '11px', lineHeight: '1.4' }}>
                      {(() => {
                        const qty = item.qty_per_unit;
                        if (qty == null || qty === undefined) return '0';
                        if (typeof qty !== 'number') return String(qty);
                        const unit = item.unit || '';
                        const decimals = (unit === 'g' || unit === 'ml') ? 0 : 2;
                        return qty.toFixed(decimals);
                      })()} {item.unit || ''}
                    </Text>
                    {(() => {
                      const cost = item.item_cost_rub;
                      if (cost == null || cost === undefined || cost <= 0) return null;
                      return (
                        <Tag 
                          color="success" 
                          style={{ 
                            margin: 0, 
                            fontWeight: 600,
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: 3,
                            lineHeight: '1.4'
                          }}
                        >
                          {typeof cost === 'number' ? cost.toFixed(2) : String(cost)}₽
                        </Tag>
                      );
                    })()}
                  </div>
                </div>
              );
            })}
          </div>
        );
      },
    },
    {
      title: (
        <Tooltip title="Себестоимость напитка (COGS): сумма стоимости всех учитываемых ингредиентов">
          <Space size={4}>
            <DollarOutlined />
            <span>Себестоимость</span>
          </Space>
        </Tooltip>
      ),
      dataIndex: 'cogs_rub',
      key: 'cogs_rub',
      width: 120,
      align: 'right' as const,
      render: (cogs: number | undefined, record: Drink) => {
        if (cogs === undefined || cogs === null || (typeof cogs === 'number' && cogs === 0)) {
          return (
            <Text type="secondary" style={{ fontSize: '13px' }}>
              —
            </Text>
          );
        }
        // Определяем цвет в зависимости от себестоимости
        const getColor = (value: number) => {
          if (value < 20) return '#52c41a'; // Зеленый для низкой себестоимости
          if (value < 50) return '#1890ff'; // Синий для средней
          return '#fa8c16'; // Оранжевый для высокой
        };
        
        const cogsValue = typeof cogs === 'number' ? cogs : 0;
        
        return (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 3, padding: '4px 0' }}>
            <Text 
              strong 
              style={{ 
                color: getColor(cogsValue),
                fontSize: '15px',
                fontWeight: 600,
                lineHeight: 1.3,
                whiteSpace: 'nowrap'
              }}
            >
              {cogsValue.toFixed(2)}₽
            </Text>
            {record.items && record.items.length > 0 && (
              <Text 
                type="secondary" 
                style={{ 
                  fontSize: '10px',
                  lineHeight: 1.2,
                  whiteSpace: 'nowrap'
                }}
              >
                {record.items.filter(item => item.item_cost_rub && item.item_cost_rub > 0).length} ингр.
              </Text>
            )}
          </div>
        );
      },
      sorter: (a: Drink, b: Drink) => {
        const aCogs = a.cogs_rub || 0;
        const bCogs = b.cogs_rub || 0;
        return aCogs - bCogs;
      },
    },
    {
      title: (
        <Tooltip title="Статус рецепта: 'Активен' - рецепт доступен для использования, 'Неактивен' - рецепт скрыт">
          Статус
        </Tooltip>
      ),
      dataIndex: 'is_active',
      key: 'is_active',
      width: 90,
      align: 'center' as const,
      render: (active: boolean) => (
        <div style={{ padding: '4px 0' }}>
          <Tag color={active ? 'green' : 'red'} style={{ margin: 0 }}>
            {active ? 'Активен' : 'Неактивен'}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      fixed: 'right' as const,
      align: 'right' as const,
      render: (_: any, record: Drink) => (
        <div style={{ padding: '4px 0', display: 'flex', justifyContent: 'flex-end' }}>
          <Space size="small">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              size="small"
              style={{ padding: '0 4px' }}
            >
              Изменить
            </Button>
            <Popconfirm
              title="Удалить рецепт?"
              onConfirm={() => handleDelete(record.id)}
              okText="Да"
              cancelText="Нет"
            >
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                size="small"
                style={{ padding: '0 4px' }}
              >
                Удалить
              </Button>
            </Popconfirm>
          </Space>
        </div>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>☕ Рецепты</Title>
      <Text type="secondary">Управление рецептами напитков</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Добавить рецепт
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
        </div>

        <div style={{ marginBottom: 16, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Input.Search
            placeholder="Поиск по названию..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 250 }}
            allowClear
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="Статус"
            value={filterIsActive}
            onChange={setFilterIsActive}
            allowClear
            style={{ width: 150 }}
          >
            <Select.Option value={true}>Активен</Select.Option>
            <Select.Option value={false}>Неактивен</Select.Option>
          </Select>
          <Select
            placeholder="Группировка"
            value={groupBy}
            onChange={setGroupBy}
            style={{ width: 180 }}
          >
            <Select.Option value="none">Без группировки</Select.Option>
            <Select.Option value="base_name">По базовому названию</Select.Option>
            <Select.Option value="volume">По объему</Select.Option>
          </Select>
          <Button onClick={handleResetFilters}>
            Сбросить фильтры
          </Button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Empty description="Загрузка..." />
          </div>
        ) : filteredDrinks.length > 0 ? (
          groupedDrinks ? (
            // Отображение с группировкой
            <div>
              {Object.entries(groupedDrinks).map(([groupKey, groupDrinks]) => (
                <Card
                  key={groupKey}
                  title={
                    <span style={{ fontWeight: 'bold', fontSize: '16px' }}>
                      {groupBy === 'base_name' ? groupKey : `${groupKey}`}
                      <span style={{ marginLeft: 8, fontWeight: 'normal', fontSize: '14px', color: '#666' }}>
                        ({groupDrinks.length})
                      </span>
                    </span>
                  }
                  style={{ marginBottom: 16 }}
                  size="small"
                >
                  <Table
                    dataSource={groupDrinks}
                    columns={columns}
                    rowKey="id"
                    rowSelection={rowSelection}
                    pagination={false}
                    scroll={{ x: 'max-content' }}
                    size="small"
                  />
                </Card>
              ))}
            </div>
          ) : (
            // Обычное отображение без группировки
            <Table
              dataSource={filteredDrinks}
              columns={columns}
              rowKey="id"
              rowSelection={rowSelection}
              pagination={{ pageSize: 20 }}
              scroll={{ x: 800 }}
            />
          )
        ) : (
          <Empty description="Нет рецептов. Добавьте рецепт для начала работы." />
        )}
      </Card>

      {/* Модальное окно создания/редактирования рецепта */}
      <Modal
        title={editingDrink ? 'Редактировать рецепт' : 'Добавить рецепт'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditingDrink(null);
        }}
        onOk={() => form.submit()}
        width={700}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="Название" rules={[{ required: true, message: 'Введите название рецепта' }]}>
            <Input placeholder="Например: Капучино" />
          </Form.Item>
          <Form.Item name="is_active" label="Активен" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item label="Состав рецепта (ингредиенты)">
            <Form.List name="items">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item
                        {...restField}
                        name={[name, 'ingredient_code']}
                        rules={[{ required: true, message: 'Выберите ингредиент' }]}
                        style={{ width: 250 }}
                      >
                        <Select placeholder="Ингредиент" showSearch filterOption={(input, option) =>
                          (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }>
                          {ingredients.map(ing => (
                            <Select.Option 
                              key={ing.ingredient_code || ing.code} 
                              value={ing.ingredient_code || ing.code}
                              label={ing.display_name_ru || ing.ingredient_code || ing.code}
                            >
                              {ing.display_name_ru || ing.ingredient_code || ing.code}
                            </Select.Option>
                          ))}
                        </Select>
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'qty_per_unit']}
                        rules={[{ required: true, message: 'Введите количество' }]}
                        style={{ width: 120 }}
                      >
                        <InputNumber placeholder="Количество" min={0} step={0.1} style={{ width: '100%' }} />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'unit']}
                        rules={[{ required: true, message: 'Введите единицу' }]}
                        style={{ width: 100 }}
                      >
                        <Select placeholder="Ед.">
                          <Select.Option value="g">г</Select.Option>
                          <Select.Option value="ml">мл</Select.Option>
                          <Select.Option value="pcs">шт</Select.Option>
                        </Select>
                      </Form.Item>
                      <Button type="link" danger onClick={() => remove(name)}>
                        Удалить
                      </Button>
                    </Space>
                  ))}
                  <Form.Item>
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      Добавить ингредиент
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно массового редактирования */}
      <Modal
        title={`Массовое редактирование (${selectedRowKeys.length} рецептов)`}
        open={bulkEditModalOpen}
        onOk={handleBulkEditSubmit}
        onCancel={() => setBulkEditModalOpen(false)}
        width={500}
        okText="Применить"
        cancelText="Отмена"
      >
        <Form form={bulkEditForm} layout="vertical">
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
          <Text type="secondary">Изменения будут применены ко всем выбранным рецептам. Поля, оставленные пустыми, не будут изменены.</Text>
        </Form>
      </Modal>
    </div>
  );
};

export default RecipesPage;
