import { useEffect, useState, useMemo } from 'react';
import { 
  Card, Typography, Table, Button, Empty, message, Spin, Input, Modal, Space, 
  Form, Select, Switch, Tag, Popconfirm, Row, Col, Tabs, Divider, Badge
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SyncOutlined, 
  SearchOutlined, AppstoreOutlined, LinkOutlined, UnlinkOutlined
} from '@ant-design/icons';
import { 
  mappingApi, ButtonMatrix, ButtonMatrixWithItems, ButtonMatrixItem, 
  ButtonMatrixCreate, ButtonMatrixUpdate, ButtonMatrixItemCreate, 
  ButtonMatrixItemUpdate, TerminalMatrixMap, TerminalMatrixMapCreate, Drink
} from '../api/mapping';
import { getTerminals, VendistaTerminal } from '../api/sync';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const MatrixTemplatesPage = () => {
  // Matrices list state
  const [matrices, setMatrices] = useState<ButtonMatrix[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMatrix, setSelectedMatrix] = useState<ButtonMatrixWithItems | null>(null);
  const [matrixLoading, setMatrixLoading] = useState(false);
  
  // Modal states
  const [matrixModalOpen, setMatrixModalOpen] = useState(false);
  const [itemModalOpen, setItemModalOpen] = useState(false);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [editingMatrix, setEditingMatrix] = useState<ButtonMatrix | null>(null);
  const [editingItem, setEditingItem] = useState<ButtonMatrixItem | null>(null);
  
  // Forms
  const [matrixForm] = Form.useForm();
  const [itemForm] = Form.useForm();
  const [assignForm] = Form.useForm();
  
  // Data for dropdowns
  const [terminals, setTerminals] = useState<VendistaTerminal[]>([]);
  const [drinks, setDrinks] = useState<Drink[]>([]);
  const [assignedTerminals, setAssignedTerminals] = useState<TerminalMatrixMap[]>([]);
  
  // Filters
  const [searchText, setSearchText] = useState('');
  const [activeTab, setActiveTab] = useState('list');

  // Fetch matrices list
  const fetchMatrices = async () => {
    setLoading(true);
    try {
      const data = await mappingApi.getButtonMatrices();
      setMatrices(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки матриц');
    } finally {
      setLoading(false);
    }
  };

  // Fetch matrix details with items
  const fetchMatrixDetails = async (matrixId: number) => {
    setMatrixLoading(true);
    try {
      const data = await mappingApi.getButtonMatrix(matrixId);
      setSelectedMatrix(data);
      setActiveTab('details');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки матрицы');
    } finally {
      setMatrixLoading(false);
    }
  };

  // Fetch assigned terminals
  const fetchAssignedTerminals = async (matrixId: number) => {
    try {
      const data = await mappingApi.getMatrixTerminals(matrixId);
      setAssignedTerminals(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки терминалов');
    }
  };

  // Fetch all data
  const fetchAllData = async () => {
    try {
      const [terminalsData, drinksData] = await Promise.all([
        getTerminals().then(r => r.data),
        mappingApi.getDrinks()
      ]);
      setTerminals(terminalsData);
      setDrinks(drinksData);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки данных');
    }
  };

  useEffect(() => {
    fetchMatrices();
    fetchAllData();
  }, []);

  useEffect(() => {
    if (selectedMatrix) {
      fetchAssignedTerminals(selectedMatrix.id);
    }
  }, [selectedMatrix]);

  // Filtered matrices
  const filteredMatrices = useMemo(() => {
    return matrices.filter(matrix => {
      if (searchText) {
        const searchLower = searchText.toLowerCase();
        return (
          matrix.name.toLowerCase().includes(searchLower) ||
          matrix.description?.toLowerCase().includes(searchLower) ||
          String(matrix.id).includes(searchText)
        );
      }
      return true;
    });
  }, [matrices, searchText]);

  // Matrix CRUD handlers
  const handleCreateMatrix = () => {
    setEditingMatrix(null);
    matrixForm.resetFields();
    matrixForm.setFieldsValue({ is_active: true });
    setMatrixModalOpen(true);
  };

  const handleEditMatrix = (matrix: ButtonMatrix) => {
    setEditingMatrix(matrix);
    matrixForm.setFieldsValue({
      name: matrix.name,
      description: matrix.description,
      is_active: matrix.is_active
    });
    setMatrixModalOpen(true);
  };

  const handleSaveMatrix = async () => {
    try {
      const values = await matrixForm.validateFields();
      if (editingMatrix) {
        await mappingApi.updateButtonMatrix(editingMatrix.id, values);
        message.success('Матрица обновлена');
      } else {
        await mappingApi.createButtonMatrix(values);
        message.success('Матрица создана');
      }
      setMatrixModalOpen(false);
      matrixForm.resetFields();
      fetchMatrices();
    } catch (error: any) {
      if (error.errorFields) return;
      message.error(error.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDeleteMatrix = async (matrixId: number) => {
    try {
      await mappingApi.deleteButtonMatrix(matrixId);
      message.success('Матрица удалена');
      if (selectedMatrix?.id === matrixId) {
        setSelectedMatrix(null);
        setActiveTab('list');
      }
      fetchMatrices();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  // Item CRUD handlers
  const handleCreateItem = () => {
    if (!selectedMatrix) return;
    setEditingItem(null);
    itemForm.resetFields();
    itemForm.setFieldsValue({ is_active: true });
    setItemModalOpen(true);
  };

  const handleEditItem = (item: ButtonMatrixItem) => {
    setEditingItem(item);
    itemForm.setFieldsValue({
      machine_item_id: item.machine_item_id,
      drink_id: item.drink_id,
      is_active: item.is_active
    });
    setItemModalOpen(true);
  };

  const handleSaveItem = async () => {
    if (!selectedMatrix) return;
    try {
      const values = await itemForm.validateFields();
      if (editingItem) {
        await mappingApi.updateButtonMatrixItem(
          selectedMatrix.id,
          editingItem.machine_item_id,
          values
        );
        message.success('Элемент обновлен');
      } else {
        await mappingApi.createButtonMatrixItem(selectedMatrix.id, values);
        message.success('Элемент добавлен');
      }
      setItemModalOpen(false);
      itemForm.resetFields();
      fetchMatrixDetails(selectedMatrix.id);
    } catch (error: any) {
      if (error.errorFields) return;
      message.error(error.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDeleteItem = async (machineItemId: number) => {
    if (!selectedMatrix) return;
    try {
      await mappingApi.deleteButtonMatrixItem(selectedMatrix.id, machineItemId);
      message.success('Элемент удален');
      fetchMatrixDetails(selectedMatrix.id);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  // Terminal assignment handlers
  const handleAssignTerminals = () => {
    if (!selectedMatrix) return;
    assignForm.resetFields();
    setAssignModalOpen(true);
  };

  const handleSaveAssignments = async () => {
    if (!selectedMatrix) return;
    try {
      const values = await assignForm.validateFields();
      await mappingApi.assignTerminalsToMatrix(selectedMatrix.id, {
        vendista_term_ids: values.term_ids
      });
      message.success('Терминалы назначены');
      setAssignModalOpen(false);
      assignForm.resetFields();
      fetchAssignedTerminals(selectedMatrix.id);
    } catch (error: any) {
      if (error.errorFields) return;
      message.error(error.response?.data?.detail || 'Ошибка назначения');
    }
  };

  const handleRemoveTerminal = async (termId: number) => {
    if (!selectedMatrix) return;
    try {
      await mappingApi.removeTerminalFromMatrix(selectedMatrix.id, termId);
      message.success('Терминал удален из матрицы');
      fetchAssignedTerminals(selectedMatrix.id);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  // Matrix columns
  const matrixColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      sorter: (a: ButtonMatrix, b: ButtonMatrix) => a.name.localeCompare(b.name),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      render: (text: string | null) => text || <Text type="secondary">—</Text>,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center' as const,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Активна' : 'Неактивна'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      align: 'right' as const,
      render: (_: any, record: ButtonMatrix) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditMatrix(record)}
            size="small"
          >
            Изменить
          </Button>
          <Button
            type="link"
            onClick={() => fetchMatrixDetails(record.id)}
            size="small"
          >
            Открыть
          </Button>
          <Popconfirm
            title="Удалить матрицу?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDeleteMatrix(record.id)}
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

  // Item columns
  const itemColumns = [
    {
      title: 'Кнопка',
      dataIndex: 'machine_item_id',
      key: 'machine_item_id',
      width: 100,
      align: 'center' as const,
      sorter: (a: ButtonMatrixItem, b: ButtonMatrixItem) => a.machine_item_id - b.machine_item_id,
    },
    {
      title: 'Напиток',
      key: 'drink',
      render: (_: any, record: ButtonMatrixItem) => (
        <div>
          {record.drink_name ? (
            <>
              <div style={{ fontWeight: 500 }}>{record.drink_name}</div>
              <Text type="secondary" style={{ fontSize: '12px' }}>ID: {record.drink_id}</Text>
            </>
          ) : (
            <Text type="secondary">—</Text>
          )}
        </div>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center' as const,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Активна' : 'Неактивна'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      align: 'right' as const,
      render: (_: any, record: ButtonMatrixItem) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditItem(record)}
            size="small"
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить элемент?"
            onConfirm={() => handleDeleteItem(record.machine_item_id)}
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

  // Terminal columns
  const terminalColumns = [
    {
      title: 'ID терминала',
      dataIndex: 'vendista_term_id',
      key: 'vendista_term_id',
      width: 120,
    },
    {
      title: 'Название терминала',
      dataIndex: 'term_name',
      key: 'term_name',
      render: (text: string | null) => text || <Text type="secondary">—</Text>,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center' as const,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Активна' : 'Неактивна'}
        </Tag>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      align: 'right' as const,
      render: (_: any, record: TerminalMatrixMap) => (
        <Popconfirm
          title="Удалить терминал из матрицы?"
          onConfirm={() => handleRemoveTerminal(record.vendista_term_id)}
          okText="Да"
          cancelText="Нет"
        >
          <Button
            type="link"
            danger
            icon={<UnlinkOutlined />}
            size="small"
          >
            Удалить
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>📋 Шаблоны матриц кнопок</Title>
      <Text type="secondary">Управление шаблонами матриц и назначение терминалов</Text>

      <Tabs activeKey={activeTab} onChange={setActiveTab} style={{ marginTop: 16 }}>
        <TabPane tab="Список матриц" key="list">
          <Card>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
              <Space>
                <Input
                  placeholder="Поиск по названию, описанию..."
                  prefix={<SearchOutlined />}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  allowClear
                  style={{ width: 300 }}
                />
              </Space>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleCreateMatrix}
                >
                  Создать матрицу
                </Button>
                <Button
                  icon={<SyncOutlined />}
                  onClick={fetchMatrices}
                  loading={loading}
                >
                  Обновить
                </Button>
              </Space>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
              </div>
            ) : filteredMatrices.length > 0 ? (
              <Table
                dataSource={filteredMatrices}
                columns={matrixColumns}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            ) : (
              <Empty description="Нет матриц. Создайте новую матрицу." />
            )}
          </Card>
        </TabPane>

        {selectedMatrix && (
          <TabPane tab={`Матрица: ${selectedMatrix.name}`} key="details">
            <Card>
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleCreateItem}
                  >
                    Добавить кнопку
                  </Button>
                  <Button
                    icon={<LinkOutlined />}
                    onClick={handleAssignTerminals}
                  >
                    Назначить терминалы
                  </Button>
                  <Badge count={assignedTerminals.length} showZero>
                    <Button
                      icon={<AppstoreOutlined />}
                      onClick={() => fetchAssignedTerminals(selectedMatrix.id)}
                    >
                      Терминалы ({assignedTerminals.length})
                    </Button>
                  </Badge>
                  <Button
                    icon={<SyncOutlined />}
                    onClick={() => fetchMatrixDetails(selectedMatrix.id)}
                    loading={matrixLoading}
                  >
                    Обновить
                  </Button>
                </Space>
              </div>

              <Divider orientation="left">Информация о матрице</Divider>
              <Row gutter={16}>
                <Col span={8}>
                  <Text strong>ID:</Text> {selectedMatrix.id}
                </Col>
                <Col span={8}>
                  <Text strong>Название:</Text> {selectedMatrix.name}
                </Col>
                <Col span={8}>
                  <Text strong>Статус:</Text>{' '}
                  <Tag color={selectedMatrix.is_active ? 'green' : 'red'}>
                    {selectedMatrix.is_active ? 'Активна' : 'Неактивна'}
                  </Tag>
                </Col>
                {selectedMatrix.description && (
                  <Col span={24} style={{ marginTop: 8 }}>
                    <Text strong>Описание:</Text> {selectedMatrix.description}
                  </Col>
                )}
              </Row>

              <Divider orientation="left">Кнопки матрицы ({selectedMatrix.items.length})</Divider>
              {selectedMatrix.items.length > 0 ? (
                <Table
                  dataSource={selectedMatrix.items}
                  columns={itemColumns}
                  rowKey="machine_item_id"
                  pagination={{ pageSize: 20 }}
                />
              ) : (
                <Empty description="Нет кнопок в матрице. Добавьте кнопки." />
              )}

              <Divider orientation="left">Назначенные терминалы ({assignedTerminals.length})</Divider>
              {assignedTerminals.length > 0 ? (
                <Table
                  dataSource={assignedTerminals}
                  columns={terminalColumns}
                  rowKey="vendista_term_id"
                  pagination={{ pageSize: 20 }}
                />
              ) : (
                <Empty description="Нет назначенных терминалов. Назначьте терминалы." />
              )}
            </Card>
          </TabPane>
        )}
      </Tabs>

      {/* Matrix Modal */}
      <Modal
        title={editingMatrix ? 'Редактировать матрицу' : 'Создать матрицу'}
        open={matrixModalOpen}
        onOk={handleSaveMatrix}
        onCancel={() => {
          setMatrixModalOpen(false);
          matrixForm.resetFields();
        }}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={matrixForm} layout="vertical">
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input placeholder="Например: Jetinno JL24" />
          </Form.Item>
          <Form.Item
            name="description"
            label="Описание"
          >
            <Input.TextArea placeholder="Описание матрицы" rows={3} />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="Активна"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* Item Modal */}
      <Modal
        title={editingItem ? 'Редактировать кнопку' : 'Добавить кнопку'}
        open={itemModalOpen}
        onOk={handleSaveItem}
        onCancel={() => {
          setItemModalOpen(false);
          itemForm.resetFields();
        }}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={itemForm} layout="vertical">
          <Form.Item
            name="machine_item_id"
            label="Номер кнопки"
            rules={[
              { required: true, message: 'Введите номер кнопки' },
              { type: 'number', min: 1, message: 'Номер кнопки должен быть больше 0' }
            ]}
          >
            <Input type="number" placeholder="Номер кнопки на терминале" disabled={!!editingItem} />
          </Form.Item>
          <Form.Item
            name="drink_id"
            label="Напиток"
          >
            <Select
              placeholder="Выберите напиток"
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={drinks.map(d => ({
                value: d.id,
                label: d.name
              }))}
            />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="Активна"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* Assign Terminals Modal */}
      <Modal
        title="Назначить терминалы"
        open={assignModalOpen}
        onOk={handleSaveAssignments}
        onCancel={() => {
          setAssignModalOpen(false);
          assignForm.resetFields();
        }}
        okText="Назначить"
        cancelText="Отмена"
        width={600}
      >
        <Form form={assignForm} layout="vertical">
          <Form.Item
            name="term_ids"
            label="Терминалы"
            rules={[{ required: true, message: 'Выберите хотя бы один терминал' }]}
          >
            <Select
              mode="multiple"
              placeholder="Выберите терминалы"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={terminals.map(t => ({
                value: t.id,
                label: t.comment || `ID: ${t.id}`
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default MatrixTemplatesPage;
