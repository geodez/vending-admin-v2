import { useEffect, useState } from 'react';
import { Card, Typography, Table, DatePicker, Button, Empty, message, Spin, Input, Select, Space, Popconfirm } from 'antd';
import { SyncOutlined, DownloadOutlined } from '@ant-design/icons';
import { transactionsApi, Transaction } from '../api/transactions';
import dayjs, { Dayjs } from 'dayjs';

const { Title, Text } = Typography;

const InventoryPage = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [dateFrom, setDateFrom] = useState<Dayjs>(dayjs().startOf('month'));
  const [dateTo, setDateTo] = useState<Dayjs>(dayjs());
  const [sumType, setSumType] = useState<'all' | 'positive' | 'non_positive'>('positive');
  const [termIdFilter, setTermIdFilter] = useState<string>('');

  const fetchTransactions = async (currentPage: number = page) => {
    setLoading(true);
    try {
      const data = await transactionsApi.getTransactions({
        date_from: dateFrom.format('YYYY-MM-DD'),
        date_to: dateTo.format('YYYY-MM-DD'),
        sum_type: sumType,
        term_id: termIdFilter ? parseInt(termIdFilter) : undefined,
        page: currentPage,
        page_size: pageSize,
      });
      setTransactions(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setPage(data.page);
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка загрузки транзакций');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await transactionsApi.exportTransactions({
        date_from: dateFrom.format('YYYY-MM-DD'),
        date_to: dateTo.format('YYYY-MM-DD'),
        sum_type: sumType,
        term_id: termIdFilter ? parseInt(termIdFilter) : undefined,
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `transactions_${dateFrom.format('YYYYMMDD')}_${dateTo.format('YYYYMMDD')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('CSV файл загружен');
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при экспорте');
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchTransactions(1);
  }, []);

  const columns = [
    {
      title: 'Дата/время',
      dataIndex: 'tx_time',
      key: 'tx_time',
      render: (value: string | null) => value ? dayjs(value).format('DD.MM.YY HH:mm') : '-',
      width: 140,
    },
    {
      title: 'Терминал',
      dataIndex: 'term_id',
      key: 'term_id',
      width: 100,
    },
    {
      title: 'Сумма',
      dataIndex: 'sum_rub',
      key: 'sum_rub',
      render: (value: number | null, record: Transaction) => {
        const total = (record.sum_kopecks || 0) / 100;
        return `${total.toFixed(2)} ₽`;
      },
      width: 100,
    },
    {
      title: 'Кнопка',
      dataIndex: 'machine_item_id',
      key: 'machine_item_id',
      render: (value: number | null) => value ?? '-',
      width: 80,
    },
    {
      title: 'Напиток',
      dataIndex: 'drink_name',
      key: 'drink_name',
      render: (value: string | null) => value || '-',
      width: 150,
    },
    {
      title: 'Комментарий',
      dataIndex: 'terminal_comment',
      key: 'terminal_comment',
      ellipsis: true,
      render: (value: string | null) => value || '-',
    },
  ];

  return (
    <div>
      <Title level={2}>📦 Склад</Title>
      <Text type="secondary">Управление складом и ингредиентами</Text>
      
      <Card style={{ marginTop: 16 }}>
        <Empty description="Раздел в разработке" />
      </Card>
    </div>
  );
};

export default InventoryPage;
