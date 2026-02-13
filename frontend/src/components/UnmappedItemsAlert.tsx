import React, { useEffect, useState } from 'react';
import { Alert, Button, List, Typography, Space, Tag } from 'antd';
import { WarningOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { mappingApi, UnmappedItem } from '../api/mapping';

const { Text } = Typography;

interface UnmappedItemsAlertProps {
    onOpenMatrix: (matrixId: number) => void;
    onRefresh?: () => void;
}

export const UnmappedItemsAlert: React.FC<UnmappedItemsAlertProps> = ({
    onOpenMatrix,
    onRefresh
}) => {
    const [items, setItems] = useState<UnmappedItem[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchItems = async () => {
        setLoading(true);
        try {
            const data = await mappingApi.getUnmappedItems();
            setItems(data);
        } catch (error) {
            console.error('Failed to fetch unmapped items', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, [onRefresh]);

    if (items.length === 0) return null;

    return (
        <Alert
            message={
                <Space>
                    <WarningOutlined />
                    <Text strong>Обнаружены нераспределенные позиции ({items.length})</Text>
                </Space>
            }
            description={
                <div style={{ marginTop: 8 }}>
                    <Text>
                        В транзакциях найдены кнопки, которые не привязаны к напиткам.
                        Это влияет на точность расчета прибыли.
                    </Text>
                    <div style={{ maxHeight: 200, overflowY: 'auto', marginTop: 8, marginBottom: 8 }}>
                        <List
                            size="small"
                            dataSource={items}
                            renderItem={item => (
                                <List.Item
                                    actions={[
                                        item.matrix_id ? (
                                            <Button
                                                size="small"
                                                type="link"
                                                onClick={() => onOpenMatrix(item.matrix_id!)}
                                            >
                                                Перейти к матрице <ArrowRightOutlined />
                                            </Button>
                                        ) : (
                                            <Tag color="orange">Терминал не привязан</Tag>
                                        )
                                    ]}
                                >
                                    <Space>
                                        <Text strong>Кнопка #{item.machine_item_id}</Text>
                                        <Text type="secondary">
                                            {item.term_name || `Терминал ${item.term_id}`}
                                        </Text>
                                    </Space>
                                </List.Item>
                            )}
                        />
                    </div>
                </div>
            }
            type="warning"
            showIcon={false}
            style={{ marginBottom: 16 }}
        />
    );
};
