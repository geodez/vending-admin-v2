import React, { useEffect, useState } from 'react';
import { Modal, Form, Select, InputNumber, DatePicker, Input, message } from 'antd';
import dayjs from 'dayjs';
import { getIngredients, getLocations } from '../../api/business';
import { inventoryApi } from '../../api/inventory';
import type { Ingredient, Location } from '../../types/api';

interface AddLoadModalProps {
    visible: boolean;
    onCancel: () => void;
    onSuccess: () => void;
}

export const AddLoadModal: React.FC<AddLoadModalProps> = ({ visible, onCancel, onSuccess }) => {
    const [form] = Form.useForm();
    const [loading, setLoading] = useState(false);
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [locations, setLocations] = useState<Location[]>([]);
    const [selectedIngredient, setSelectedIngredient] = useState<Ingredient | null>(null);

    useEffect(() => {
        if (visible) {
            fetchData();
            form.resetFields();
            form.setFieldsValue({
                load_date: dayjs(),
            });
            setSelectedIngredient(null);
        }
    }, [visible]);

    const fetchData = async () => {
        try {
            const [ingredientsRes, locationsRes] = await Promise.all([
                getIngredients(),
                getLocations(),
            ]);
            // Handle potential different response structures (if wrapped in data or direct array)
            const ingData = Array.isArray(ingredientsRes) ? ingredientsRes : (ingredientsRes as any).data || [];
            const locData = Array.isArray(locationsRes) ? locationsRes : (locationsRes as any).data || [];

            setIngredients(ingData);
            setLocations(locData);
        } catch (error) {
            console.error('Failed to fetch data', error);
            message.error('Ошибка загрузки данных');
        }
    };

    const handleIngredientChange = (code: string) => {
        const ingredient = ingredients.find(i => {
            const item = i as any;
            return (item.code || item.ingredient_code) === code;
        });
        setSelectedIngredient(ingredient || null);
    };

    const handleSubmit = async () => {
        try {
            const values = await form.validateFields();
            setLoading(true);

            if (!selectedIngredient) {
                message.error('Выберите ингредиент');
                setLoading(false);
                return;
            }

            const item = selectedIngredient as any;
            const unit = item.unit || item.unit_ru || 'pcs';

            await inventoryApi.createIngredientLoad({
                ingredient_code: values.ingredient_code,
                location_id: values.location_id,
                load_date: values.load_date.format('YYYY-MM-DD'),
                qty: values.qty,
                unit: unit,
                comment: values.comment,
            });

            message.success('Загрузка добавлена');
            onSuccess();
        } catch (error: any) {
            if (error.errorFields) {
                return; // Validation error
            }
            message.error(error.response?.data?.detail || 'Ошибка сохранения');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            title="Добавить загрузку ингредиентов"
            open={visible}
            onOk={handleSubmit}
            onCancel={onCancel}
            confirmLoading={loading}
            okText="Сохранить"
            cancelText="Отмена"
        >
            <Form
                form={form}
                layout="vertical"
            >
                <Form.Item
                    name="location_id"
                    label="Локация"
                    rules={[{ required: true, message: 'Выберите локацию' }]}
                >
                    <Select placeholder="Выберите локацию">
                        {locations.map(loc => (
                            <Select.Option key={loc.id} value={loc.id}>
                                {loc.name}
                            </Select.Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item
                    name="ingredient_code"
                    label="Ингредиент"
                    rules={[{ required: true, message: 'Выберите ингредиент' }]}
                >
                    <Select
                        placeholder="Выберите ингредиент"
                        showSearch
                        optionFilterProp="children"
                        onChange={handleIngredientChange}
                    >
                        {ingredients.map(ing => {
                            const item = ing as any;
                            const code = item.code || item.ingredient_code;
                            const name = item.name_ru || item.display_name_ru || item.name;
                            return (
                                <Select.Option key={code} value={code}>
                                    {name} ({code})
                                </Select.Option>
                            );
                        })}
                    </Select>
                </Form.Item>

                <Form.Item
                    label="Единица измерения"
                >
                    <Input value={(selectedIngredient as any)?.unit_ru || (selectedIngredient as any)?.unit || '-'} disabled />
                </Form.Item>

                <Form.Item
                    name="qty"
                    label="Количество"
                    rules={[{ required: true, message: 'Введите количество' }]}
                >
                    <InputNumber
                        style={{ width: '100%' }}
                        min={0}
                        step={0.1}
                        placeholder="0.00"
                    />
                </Form.Item>

                <Form.Item
                    name="load_date"
                    label="Дата загрузки"
                    rules={[{ required: true, message: 'Выберите дату' }]}
                >
                    <DatePicker style={{ width: '100%' }} />
                </Form.Item>

                <Form.Item
                    name="comment"
                    label="Комментарий"
                >
                    <Input.TextArea rows={2} />
                </Form.Item>
            </Form>
        </Modal>
    );
};
