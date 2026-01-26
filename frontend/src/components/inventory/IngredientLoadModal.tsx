import { useEffect, useState } from 'react';
import { Modal, Form, Input, InputNumber, Select, DatePicker, message } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { inventoryApi, IngredientLoadCreate } from '../../api/inventory';
import { getIngredients } from '../../api/business';
import { getLocations } from '../../api/business';
import type { Ingredient, Location } from '@/types/api';

interface IngredientLoadModalProps {
  open: boolean;
  onCancel: () => void;
  onSuccess: () => void;
  initialValues?: Partial<IngredientLoadCreate>;
}

const IngredientLoadModal = ({ open, onCancel, onSuccess, initialValues }: IngredientLoadModalProps) => {
  const [form] = Form.useForm();
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      loadData();
      if (initialValues) {
        form.setFieldsValue({
          ...initialValues,
          load_date: initialValues.load_date ? dayjs(initialValues.load_date) : dayjs(),
        });
      } else {
        form.resetFields();
        form.setFieldsValue({
          load_date: dayjs(),
        });
      }
    }
  }, [open, initialValues]);

  const loadData = async () => {
    try {
      const [ingredientsRes, locationsRes] = await Promise.all([
        getIngredients(),
        getLocations(),
      ]);
      setIngredients(Array.isArray(ingredientsRes.data) ? ingredientsRes.data : []);
      setLocations(Array.isArray(locationsRes.data) ? locationsRes.data : []);
    } catch (error: any) {
      message.error('Ошибка загрузки данных');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data: IngredientLoadCreate = {
        ...values,
        load_date: values.load_date.format('YYYY-MM-DD'),
      };

      setLoading(true);
      await inventoryApi.createIngredientLoad(data);
      message.success('Загрузка добавлена');
      form.resetFields();
      onSuccess();
    } catch (error: any) {
      if (error.errorFields) {
        // Validation errors
        return;
      }
      message.error(error.response?.data?.detail || 'Ошибка создания загрузки');
    } finally {
      setLoading(false);
    }
  };

  // Получить единицу измерения для выбранного ингредиента
  const selectedIngredient = Form.useWatch('ingredient_code', form);
  const ingredient = ingredients.find(i => (i.code || i.ingredient_code) === selectedIngredient);
  const unit = ingredient?.unit_ru || ingredient?.unit || '';

  return (
    <Modal
      title="Добавить загрузку ингредиента"
      open={open}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      okText="Сохранить"
      cancelText="Отмена"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="location_id"
          label="Локация"
          rules={[{ required: true, message: 'Выберите локацию' }]}
        >
          <Select placeholder="Выберите локацию" showSearch>
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
          <Select placeholder="Выберите ингредиент" showSearch>
            {ingredients
              .filter(i => i.expense_kind === 'stock_tracked')
              .map(ing => (
                <Select.Option key={ing.code || ing.ingredient_code} value={ing.code || ing.ingredient_code}>
                  {ing.name_ru || ing.display_name_ru || ing.name || ing.code || ing.ingredient_code}
                </Select.Option>
              ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="load_date"
          label="Дата загрузки"
          rules={[{ required: true, message: 'Выберите дату' }]}
        >
          <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="qty"
          label={`Количество (${unit})`}
          rules={[
            { required: true, message: 'Введите количество' },
            { type: 'number', min: 0.01, message: 'Количество должно быть больше 0' },
          ]}
        >
          <InputNumber min={0.01} step={0.01} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="unit"
          label="Единица измерения"
          rules={[{ required: true, message: 'Введите единицу измерения' }]}
        >
          <Input placeholder="кг, л, шт и т.д." />
        </Form.Item>

        <Form.Item name="comment" label="Комментарий">
          <Input.TextArea rows={3} placeholder="Необязательно" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default IngredientLoadModal;
