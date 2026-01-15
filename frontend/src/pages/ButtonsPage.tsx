import { useEffect, useState } from 'react';
import { Card, Typography, Table, Button, Empty, message, Spin, Input, Modal } from 'antd';
import { SyncOutlined, UploadOutlined, DeleteOutlined } from '@ant-design/icons';
import { mappingApi, MachineMatrix, MachineMatrixCreate } from '../api/mapping';

const { Title, Text } = Typography;
const { TextArea } = Input;

const ButtonsPage = () => {
  const [matrix, setMatrix] = useState<MachineMatrix[]>([]);
  const [loading, setLoading] = useState(false);
  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [bulkData, setBulkData] = useState('');

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

  const handleBulkUpload = async () => {
    try {
      // Parse CSV: term_id,machine_item_id,drink_id,location_id
      const lines = bulkData.trim().split('\n');
      const items: MachineMatrixCreate[] = [];

      for (const line of lines) {
        if (!line.trim() || line.startsWith('#')) continue;
        const [term_id, machine_item_id, drink_id, location_id] = line.split(',').map(s => parseInt(s.trim()));
        if (term_id && machine_item_id && drink_id && location_id) {
          items.push({ term_id, machine_item_id, drink_id, location_id, is_active: true });
        }
      }

      if (items.length === 0) {
        message.error('Нет валидных строк для импорта');
        return;
      }

      await mappingApi.bulkCreateMachineMatrix(items);
      message.success(`Импортировано записей: ${items.length}`);
      setBulkModalOpen(false);
      setBulkData('');
      fetchMatrix();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка импорта');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Терминал',
      dataIndex: 'term_id',
      key: 'term_id',
      sorter: (a: MachineMatrix, b: MachineMatrix) => a.term_id - b.term_id,
    },
    {
      title: 'Кнопка',
      dataIndex: 'machine_item_id',
      key: 'machine_item_id',
    },
    {
      title: 'Напиток ID',
      dataIndex: 'drink_id',
      key: 'drink_id',
    },
    {
      title: 'Локация',
      dataIndex: 'location_id',
      key: 'location_id',
    },
    {
      title: 'Активен',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (value: boolean) => value ? '✓' : '✗',
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: MachineMatrix) => (
        <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>🔘 Кнопки / Сопоставление</Title>
      <Text type="secondary">Сопоставление кнопок терминалов с напитками (machine_matrix)</Text>
      
      <Card style={{ marginTop: 16 }}>
        <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={fetchMatrix}
            loading={loading}
          >
            Обновить
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={() => setBulkModalOpen(true)}
          >
            Bulk Import
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
          />
        ) : (
          <Empty description="Нет сопоставлений. Без machine_matrix KPI views не будут полными. Используйте Bulk Import." />
        )}
      </Card>

      <Modal
        title="Bulk Import (CSV)"
        open={bulkModalOpen}
        onCancel={() => setBulkModalOpen(false)}
        onOk={handleBulkUpload}
        width={600}
      >
        <p>Формат: term_id,machine_item_id,drink_id,location_id (по одной записи на строку)</p>
        <TextArea
          rows={10}
          value={bulkData}
          onChange={(e) => setBulkData(e.target.value)}
          placeholder="145912,114,1,1&#10;145912,115,2,1&#10;..."
        />
      </Modal>
    </div>
  );
};

export default ButtonsPage;
