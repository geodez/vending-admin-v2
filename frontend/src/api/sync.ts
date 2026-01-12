/**
 * API module for Vendista synchronization
 */
import apiClient from './client';

export interface SyncStatus {
  terminal_id: number;
  last_sync_time: string | null;
  last_sync_status: string | null;
  error_message: string | null;
  transactions_count: number;
}

export interface VendistaTerminal {
  id: number;
  vendista_term_id: number;
  title: string;
  comment: string | null;
  is_active: boolean;
  location_id: number | null;
}

export interface VendistaTransaction {
  id: number;
  term_id: number;
  vendista_tx_id: number;
  tx_time: string;
  payload: any;
}

// Trigger manual sync
export const triggerSync = (params?: { terminal_id?: number; force?: boolean }) =>
  apiClient.post<{ message: string; synced_count: number }>('/api/v1/sync/sync', null, { params });

// Get sync status
export const getSyncStatus = (terminalId?: number) =>
  apiClient.get<SyncStatus[]>('/api/v1/sync/status', { params: { terminal_id: terminalId } });

// Get terminals
export const getTerminals = () =>
  apiClient.get<VendistaTerminal[]>('/api/v1/sync/terminals');

// Get transactions
export const getTransactions = (params?: {
  terminal_id?: number;
  from_date?: string;
  to_date?: string;
  limit?: number;
  offset?: number;
}) => apiClient.get<VendistaTransaction[]>('/api/v1/sync/transactions', { params });

// Get transaction count
export const getTransactionCount = (params?: {
  terminal_id?: number;
  from_date?: string;
  to_date?: string;
}) => apiClient.get<{ count: number }>('/api/v1/sync/transactions/count', { params });
