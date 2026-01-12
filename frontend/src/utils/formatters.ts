import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import { DATE_FORMAT, DATETIME_FORMAT } from './constants';

dayjs.locale('ru');

/**
 * Форматирование числа с разделителями тысяч
 */
export const formatNumber = (value: number | null | undefined, decimals: number = 0): string => {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Форматирование валюты (рубли)
 */
export const formatCurrency = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * Форматирование процентов
 */
export const formatPercent = (value: number | null | undefined, decimals: number = 1): string => {
  if (value === null || value === undefined) return '—';
  return `${formatNumber(value, decimals)}%`;
};

/**
 * Форматирование даты
 */
export const formatDate = (date: string | Date | null | undefined, format: string = DATE_FORMAT): string => {
  if (!date) return '—';
  return dayjs(date).format(format);
};

/**
 * Форматирование даты и времени
 */
export const formatDateTime = (date: string | Date | null | undefined): string => {
  return formatDate(date, DATETIME_FORMAT);
};

/**
 * Относительное время (например, "2 часа назад")
 */
export const formatRelativeTime = (date: string | Date | null | undefined): string => {
  if (!date) return '—';
  const now = dayjs();
  const target = dayjs(date);
  const diffMinutes = now.diff(target, 'minute');
  
  if (diffMinutes < 1) return 'только что';
  if (diffMinutes < 60) return `${diffMinutes} мин. назад`;
  
  const diffHours = now.diff(target, 'hour');
  if (diffHours < 24) return `${diffHours} ч. назад`;
  
  const diffDays = now.diff(target, 'day');
  if (diffDays < 7) return `${diffDays} дн. назад`;
  
  return formatDate(date);
};

/**
 * Форматирование единиц измерения
 */
export const formatUnit = (value: number, unit: string): string => {
  return `${formatNumber(value, unit === 'г' || unit === 'мл' ? 0 : 2)} ${unit}`;
};

/**
 * Сокращение больших чисел (1000 -> 1K, 1000000 -> 1M)
 */
export const formatCompactNumber = (value: number): string => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return formatNumber(value);
};

/**
 * Цвет для значения (положительное - зелёный, отрицательное - красный)
 */
export const getValueColor = (value: number): 'success' | 'danger' | 'default' => {
  if (value > 0) return 'success';
  if (value < 0) return 'danger';
  return 'default';
};

/**
 * Форматирование статуса алерта
 */
export const getAlertColor = (severity: 'critical' | 'warning' | 'info'): 'error' | 'warning' | 'info' => {
  const map = {
    critical: 'error' as const,
    warning: 'warning' as const,
    info: 'info' as const,
  };
  return map[severity];
};

/**
 * Форматирование роли пользователя
 */
export const formatRole = (role: 'owner' | 'operator'): string => {
  const map = {
    owner: 'Собственник',
    operator: 'Оператор',
  };
  return map[role] || role;
};
