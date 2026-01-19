import { useEffect, useState, useMemo } from 'react';
import { 
  Card, Typography, Table, Button, Empty, message, Spin, Input, Modal, Upload, Alert, Space, 
  Form, Select, Switch, Tag, Popconfirm, Row, Col, Badge
} from 'antd';
import { 
  SyncOutlined, UploadOutlined, DeleteOutlined, PlusOutlined, EditOutlined, 
  SearchOutlined, CheckSquareOutlined
} from '@ant-design/icons';
import { mappingApi, MachineMatrix, ImportPreviewResponse, ImportApplyResponse, MachineMatrixCreate, Drink } from '../api/mapping';
import { getTerminals, VendistaTerminal } from '../api/sync';
import { getLocations } from '../api/business';
import type { Location } from '@/types/api';
import type { UploadFile } from 'antd';

const { Title, Text } = Typography;

const ButtonsPage = () => {
  const [matrix, setMatrix] = useState<MachineMatrix[]>([]);
  const [loading, setLoading] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<MachineMatrix | null>(null);
  const [form] = Form.useForm();
  
  // Import modal state
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [importStep, setImportStep] = useState<'upload' | 'preview' | 'applying'>('upload');
  
  // Data for dropdowns
  const [terminals, setTerminals] = useState<VendistaTerminal[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [drinks, setDrinks] = useState<Drink[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  
  // Filters
  const [searchText, setSearchText] = useState('');
  const [filterTermId, setFilterTermId] = useState<number | undefined>();
  const [filterDrinkId, setFilterDrinkId] = useState<number | undefined>();
  const [filterLocationId, setFilterLocationId] = useState<number | undefined>();
  const [filterIsActive, setFilterIsActive] = useState<boolean | undefined>();
  
  // Selection
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [bulkEditModalOpen, setBulkEditModalOpen] = useState(false);

  // Fetch all data
  const fetchAllData = async () => {
    setLoadingData(true);
    try {
      const [matrixData, terminalsData, locationsData, drinksData] = await Promise.all([
        mappingApi.getMachineMatrix(),
        getTerminals().then(r => r.data),
        getLocations().then(r => r.data),
        mappingApi.getDrinks()
      ]);
      setMatrix(matrixData);
      setTerminals(terminalsData);
      setLocations(locationsData);
      setDrinks(drinksData);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  // Filtered matrix
  const filteredMatrix = useMemo(() => {
    return matrix.filter(item => {
      if (searchText) {
        const searchLower = searchText.toLowerCase();
        const matchesSearch = 
          item.term_name?.toLowerCase().includes(searchLower) ||
          item.drink_name?.toLowerCase().includes(searchLower) ||
          item.location_name?.toLowerCase().includes(searchLower) ||
          String(item.term_id).includes(searchText) ||
          String(item.machine_item_id).includes(searchText);
        if (!matchesSearch) return false;
      }
      if (filterTermId !== undefined && item.term_id !== filterTermId) return false;
      if (filterDrinkId !== undefined && item.drink_id !== filterDrinkId) return false;
      if (filterLocationId !== undefined && item.location_id !== filterLocationId) return false;
      if (filterIsActive !== undefined && item.is_active !== filterIsActive) return false;
      return true;
    });
  }, [matrix, searchText, filterTermId, filterDrinkId, filterLocationId, filterIsActive]);

  const handleCreate = () => {
    setEditingRecord(null);
    form.resetFields();
    form.setFieldsValue({
      is_active: true
    });
    setEditModalOpen(true);
  };

  const handleEdit = (record: MachineMatrix) => {
    setEditingRecord(record);
    form.setFieldsValue({
      term_id: record.term_id,
      machine_item_id: record.machine_item_id,
      drink_id: record.drink_id,
      location_id: record.location_id,
      is_active: record.is_active
    });
    setEditModalOpen(true);
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const data: MachineMatrixCreate = {
        term_id: values.term_id,
        machine_item_id: values.machine_item_id,
        drink_id: values.drink_id,
        location_id: values.location_id,
        is_active: values.is_active ?? true
      };
      
      await mappingApi.createMachineMatrix(data);
      message.success(editingRecord ? 'Запись обновлена' : 'Запись создана');
      setEditModalOpen(false);
      form.resetFields();
      fetchAllData();
    } catch (error: any) {
      if (error.errorFields) {
        // Form validation errors
        return;
      }
      message.error(error.response?.data?.detail || 'Ошибка сохранения');
    }
  };

  const handleDelete = async (record: MachineMatrix) => {
    try {
      await mappingApi.deleteMachineMatrix(record.term_id, record.machine_item_id);
      message.success('Запись удалена');
      fetchAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleBulkEdit = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите записи для редактирования');
      return;
    }
    setBulkEditModalOpen(true);
  };

  const handleBulkEditSubmit = async (values: { is_active: boolean }) => {
    try {
      const selectedRecords = filteredMatrix.filter(record => 
        selectedRowKeys.includes(`${record.term_id}-${record.machine_item_id}`)
      );
      
      const updates = selectedRecords.map(record => ({
        term_id: record.term_id,
        machine_item_id: record.machine_item_id,
        drink_id: record.drink_id!,
        location_id: record.location_id!,
        is_active: values.is_active
      }));
      
      await mappingApi.bulkCreateMachineMatrix(updates);
      message.success(`Обновлено записей: ${updates.length}`);
      setBulkEditModalOpen(false);
      setSelectedRowKeys([]);
      fetchAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка массового обновления');
    }
  };

  const handleBulkDelete = async () => {
    try {
      const selectedRecords = filteredMatrix.filter(record => 
        selectedRowKeys.includes(`${record.term_id}-${record.machine_item_id}`)
      );
      
      await Promise.all(
        selectedRecords.map(record => 
          mappingApi.deleteMachineMatrix(record.term_id, record.machine_item_id)
        )
      );
      
      message.success(`Удалено записей: ${selectedRecords.length}`);
      setSelectedRowKeys([]);
      fetchAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка массового удаления');
    }
  };

  const handleFileSelect = async (files: UploadFile[]) => {
    if (files.length === 0) return;
    
    const file = files[0].originFileObj as File;
    setUploadedFile(file);
    handleDryRun(file);
  };

  const handleDryRun = async (file: File) => {
    setPreviewLoading(true);
    try {
      const preview = await mappingApi.dryRunImport(file);
      setPreviewData(preview);
      setImportStep('preview');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при проверке CSV');
      setImportStep('upload');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleApplyImport = async () => {
    if (!uploadedFile) {
      message.error('Файл не выбран');
      return;
    }

    setApplyLoading(true);
    setImportStep('applying');
    try {
      const result = await mappingApi.applyImport(uploadedFile);
      message.success(`Импортировано: ${result.inserted} записей`);
      setImportModalOpen(false);
      setUploadedFile(null);
      setPreviewData(null);
      setImportStep('upload');
      fetchAllData();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при импорте');
      setImportStep('preview');
    } finally {
      setApplyLoading(false);
    }
  };

  const handleCloseImportModal = () => {
    setImportModalOpen(false);
    setUploadedFile(null);
    setPreviewData(null);
    setImportStep('upload');
  };

  const handleResetFilters = () => {
    setSearchText('');
    setFilterTermId(undefined);
    setFilterDrinkId(undefined);
    setFilterLocationId(undefined);
    setFilterIsActive(undefined);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  };

  const columns = [
    {
      title: 'Терминал',
      key: 'term',
      width: 180,
      sorter: (a: MachineMatrix, b: MachineMatrix) => (a.term_name || '').localeCompare(b.term_name || ''),
      render: (_: any, record: MachineMatrix) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.term_name || `ID: ${record.term_id}`}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>ID: {record.term_id}</Text>
        </div>
      ),
    },
    {
      title: 'Кнопка',
      dataIndex: 'machine_item_id',
      key: 'machine_item_id',
      width: 80,
      align: 'center' as const,
      sorter: (a: MachineMatrix, b: MachineMatrix) => a.machine_item_id - b.machine_item_id,
    },
    {
      title: 'Напиток',
      key: 'drink',
      width: 200,
      sorter: (a: MachineMatrix, b: MachineMatrix) => (a.drink_name || '').localeCompare(b.drink_name || ''),
      render: (_: any, record: MachineMatrix) => (
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
      title: 'Локация',
      key: 'location',
      width: 150,
      sorter: (a: MachineMatrix, b: MachineMatrix) => (a.location_name || '').localeCompare(b.location_name || ''),
      render: (_: any, record: MachineMatrix) => (
        <div>
          {record.location_name ? (
            <>
              <div style={{ fontWeight: 500 }}>{record.location_name}</div>
              <Text type="secondary" style={{ fontSize: '12px' }}>ID: {record.location_id}</Text>
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
      width: 120,
      align: 'right' as const,
      render: (_: any, record: MachineMatrix) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить сопоставление?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDelete(record)}
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

  return (
    <div>
      <Title level={2}>🔘 Кнопки / Сопоставление</Title>
      <Text type="secondary">Сопоставление кнопок терминалов с напитками</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Добавить сопоставление
            </Button>
            {selectedRowKeys.length > 0 && (
              <>
                <Badge count={selectedRowKeys.length} showZero>
                  <Button
                    icon={<CheckSquareOutlined />}
                    onClick={handleBulkEdit}
                  >
                    Массовое редактирование
                  </Button>
                </Badge>
                <Popconfirm
                  title={`Удалить ${selectedRowKeys.length} записей?`}
                  description="Это действие нельзя отменить"
                  onConfirm={handleBulkDelete}
                  okText="Да"
                  cancelText="Нет"
                >
                  <Button danger icon={<DeleteOutlined />}>
                    Удалить выбранные
                  </Button>
                </Popconfirm>
              </>
            )}
            <Button
              icon={<SyncOutlined />}
              onClick={fetchAllData}
              loading={loading}
            >
              Обновить
            </Button>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setImportModalOpen(true)}
            >
              Импорт CSV
            </Button>
          </Space>
        </div>

        {/* Filters */}
        <div style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Input
                placeholder="Поиск по терминалу, напитку, локации..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="Терминал"
                style={{ width: '100%' }}
                allowClear
                value={filterTermId}
                onChange={setFilterTermId}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={terminals.map(t => ({
                  value: t.id,
                  label: t.comment || `ID: ${t.id}`
                }))}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="Напиток"
                style={{ width: '100%' }}
                allowClear
                value={filterDrinkId}
                onChange={setFilterDrinkId}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={drinks.map(d => ({
                  value: d.id,
                  label: d.name
                }))}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="Локация"
                style={{ width: '100%' }}
                allowClear
                value={filterLocationId}
                onChange={setFilterLocationId}
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={locations.map(l => ({
                  value: l.id,
                  label: l.name
                }))}
              />
            </Col>
            <Col span={3}>
              <Select
                placeholder="Статус"
                style={{ width: '100%' }}
                allowClear
                value={filterIsActive}
                onChange={setFilterIsActive}
                options={[
                  { value: true, label: 'Активна' },
                  { value: false, label: 'Неактивна' }
                ]}
              />
            </Col>
            <Col span={3}>
              <Button onClick={handleResetFilters} block>
                Сбросить
              </Button>
            </Col>
          </Row>
        </div>

        {loading || loadingData ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : filteredMatrix.length > 0 ? (
          <Table
            dataSource={filteredMatrix}
            columns={columns}
            rowKey={(record) => `${record.term_id}-${record.machine_item_id}`}
            rowSelection={rowSelection}
            pagination={{ pageSize: 20 }}
            scroll={{ x: 1000 }}
          />
        ) : (
          <Empty description="Нет сопоставлений. Добавьте сопоставление или используйте 'Импорт CSV'." />
        )}
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingRecord ? 'Редактировать сопоставление' : 'Добавить сопоставление'}
        open={editModalOpen}
        onOk={handleSave}
        onCancel={() => {
          setEditModalOpen(false);
          form.resetFields();
        }}
        width={600}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="term_id"
            label="Терминал"
            rules={[{ required: true, message: 'Выберите терминал' }]}
          >
            <Select
              placeholder="Выберите терминал"
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

          <Form.Item
            name="machine_item_id"
            label="Номер кнопки"
            rules={[
              { required: true, message: 'Введите номер кнопки' },
              { type: 'number', min: 1, message: 'Номер кнопки должен быть больше 0' }
            ]}
          >
            <Input type="number" placeholder="Номер кнопки на терминале" />
          </Form.Item>

          <Form.Item
            name="drink_id"
            label="Напиток"
            rules={[{ required: true, message: 'Выберите напиток' }]}
          >
            <Select
              placeholder="Выберите напиток"
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
            name="location_id"
            label="Локация"
            rules={[{ required: true, message: 'Выберите локацию' }]}
          >
            <Select
              placeholder="Выберите локацию"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={locations.map(l => ({
                value: l.id,
                label: l.name
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

      {/* Bulk Edit Modal */}
      <Modal
        title="Массовое редактирование"
        open={bulkEditModalOpen}
        onOk={() => {
          form.validateFields().then(values => {
            handleBulkEditSubmit(values);
          });
        }}
        onCancel={() => setBulkEditModalOpen(false)}
        okText="Применить"
        cancelText="Отмена"
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            name="is_active"
            label="Статус активности"
          >
            <Switch checkedChildren="Активна" unCheckedChildren="Неактивна" />
          </Form.Item>
          <Text type="secondary">
            Будет обновлено записей: {selectedRowKeys.length}
          </Text>
        </Form>
      </Modal>

      {/* Import Modal */}
      <Modal
        title="Импорт CSV (machine_matrix)"
        open={importModalOpen}
        onCancel={handleCloseImportModal}
        footer={
          importStep === 'upload' ? [
            <Button key="cancel" onClick={handleCloseImportModal}>
              Отмена
            </Button>,
          ] : importStep === 'preview' ? [
            <Button key="cancel" onClick={handleCloseImportModal}>
              Отмена
            </Button>,
            <Button
              key="apply"
              type="primary"
              loading={applyLoading}
              onClick={handleApplyImport}
              danger
            >
              Применить
            </Button>,
          ] : null
        }
        width={700}
      >
        {importStep === 'upload' && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message="Формат CSV"
              description="term_id,machine_item_id,drink_id,location_id,is_active"
              type="info"
              showIcon
            />
            <Alert
              message="Пример"
              description="178428,1,101,10,true"
              type="info"
              showIcon
            />
            <Upload
              accept=".csv"
              maxCount={1}
              beforeUpload={() => false}
              onChange={(info) => handleFileSelect(info.fileList)}
            >
              <Button icon={<UploadOutlined />} loading={previewLoading}>
                Выбрать CSV файл
              </Button>
            </Upload>
          </Space>
        )}

        {importStep === 'preview' && previewData && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Alert
              message={`Проверка CSV: ${previewData.valid_rows} валидных строк`}
              type={previewData.errors.length === 0 ? 'success' : 'warning'}
              showIcon
            />
            {previewData.errors.length > 0 && (
              <Alert
                message={`Ошибки: ${previewData.errors.length}`}
                description={previewData.errors.slice(0, 5).map(e => `Строка ${e.row}: ${e.error}`).join('\n')}
                type="error"
                showIcon
              />
            )}
            <Text strong>Превью (первые 100 строк):</Text>
            <div style={{ maxHeight: 300, overflow: 'auto', border: '1px solid #d9d9d9', borderRadius: 4, padding: 8 }}>
              <Table
                dataSource={previewData.preview}
                columns={[
                  { title: 'Терминал', dataIndex: 'term_id', key: 'term_id' },
                  { title: 'Кнопка', dataIndex: 'machine_item_id', key: 'machine_item_id' },
                  { title: 'Напиток', dataIndex: 'drink_id', key: 'drink_id' },
                  { title: 'Локация', dataIndex: 'location_id', key: 'location_id' },
                  { title: 'Активна', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => v ? '✓' : '✗' },
                ]}
                pagination={false}
                size="small"
                rowKey={(_, idx) => idx}
              />
            </div>
          </Space>
        )}

        {importStep === 'applying' && (
          <Spin tip="Применение изменений..." />
        )}
      </Modal>
    </div>
  );
};

export default ButtonsPage;
