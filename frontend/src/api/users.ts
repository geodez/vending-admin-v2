/**
 * API module for user management (Owner only)
 */
import apiClient from './client';
import type { User } from '@/types/api';

export const getUsers = () =>
  apiClient.get<User[]>('/v1/users');

export const getUser = (userId: number) =>
  apiClient.get<User>(`/v1/users/${userId}`);

export const createUser = (data: {
  telegram_user_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  role: 'owner' | 'operator';
}) => apiClient.post<User>('/v1/users', data);

export const updateUser = (userId: number, data: {
  role?: 'owner' | 'operator';
  is_active?: boolean;
}) => apiClient.put<User>(`/v1/users/${userId}`, data);

export const deleteUser = (userId: number) =>
  apiClient.delete(`/v1/users/${userId}`);
