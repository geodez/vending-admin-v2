import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Empty, message, Spin, Input, Modal, Upload, Alert, Space } from 'antd';
import { SyncOutlined, UploadOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { mappingApi, MachineMatrix, ImportPreviewResponse, ImportApplyResponse } from '../api/mapping';
import type { UploadFile } from 'antd';

const { Title, Text } = Typography;
const { TextArea } = Input;

const ButtonsPage = () => {
  const [matrix, setMatrix] = useState<MachineMatrix[]>([]);
  const [loading, setLoading] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<ImportPreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [importStep, setImportStep] = useState<'upload' | 'preview' | 'applying'>('upload');

  const fetchMatrix = async () => {
    setLoading(true);
    try {
      const data = await mappingApi.getMachineMatrix();
      setMatrix(data);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки матрицы');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatrix();
  }, []);

  const handleDelete = async (id: number) => {
    try {
      await mappingApi.deleteMachineMatrix(id);
      message.success('Запись удалена');
      fetchMatrix();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка удаления');
    }
  };

  const handleFileSelect = async (files: UploadFile[]) => {
    if (files.length === 0) return;
    
    const file = files[0].originFileObj as File;
    setUploadedFile(file);
    
    // Automatically trigger dry-run
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
      fetchMatrix();
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

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 50,
    },
    {
      title: 'Терминал',
      dataIndex: 'term_id',
      key: 'term_id',
      sorter: (a: MachineMatrix, b: MachineMatrix) => a.term_id - b.term_id,
      width: 100,
    },
    {
      title: 'Кнопка',
      dataIndex: 'machine_item_id',
      key: 'machine_item_id',
      width: 80,
    },
    {
      title: 'Напиток ID',
      dataIndex: 'drink_id',
      key: 'drink_id',
      width: 80,
    },
    {
      title: 'Локация',
      dataIndex: 'location_id',
      key: 'location_id',
      width: 80,
    },
    {
      title: 'Активен',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => value ? '✓' : '✗',
      width: 70,
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: MachineMatrix) => (
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
      ),
      width: 80,
    },
  ];

  return (
    <div>
      <Title level={2}>🔘 Кнопки / Сопоставление</Title>
      <Text type="secondary">Сопоставление кнопок терминалов с напитками (machine_matrix)</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={fetchMatrix}
            loading={loading}
            style={{ marginRight: 8 }}
          >
            Обновить
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={() => setImportModalOpen(true)}
          >
            Импорт CSV
          </Button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
          </div>
        ) : matrix.length > 0 ? (
          <Table
            dataSource={matrix}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 20 }}
            scroll={{ x: 800 }}
          />
        ) : (
          <Empty description="Нет сопоставлений. Используйте 'Импорт CSV' для добавления." />
        )}
      </Card>

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
              <Button icon={<UploadOutlined />}>Выбрать CSV файл</Button>
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
