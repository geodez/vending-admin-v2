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

export interface SyncRun {
  id: number;
  started_at: string | null;
  completed_at: string | null;
  period_start: string | null;
  period_end: string | null;
  fetched: number | null;
  inserted: number | null;
  skipped_duplicates: number | null;
  expected_total: number | null;
  pages_fetched: number | null;
  items_per_page: number | null;
  last_page: number | null;
  ok: boolean | null;
  message: string | null;
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
  apiClient.post<{ message: string; synced_count: number }>('/v1/sync/sync', null, { params });

// Get sync status
export const getSyncStatus = (terminalId?: number) =>
  apiClient.get<SyncStatus[]>('/v1/sync/status', { params: { terminal_id: terminalId } });

// Get terminals
export const getTerminals = () =>
  apiClient.get<VendistaTerminal[]>('/v1/sync/terminals');

// Get transactions
export const getTransactions = (params?: {
  terminal_id?: number;
  from_date?: string;
  to_date?: string;
  limit?: number;
  offset?: number;
}) => apiClient.get<VendistaTransaction[]>('/v1/sync/transactions', { params });

// Get transaction count
export const getTransactionCount = (params?: {
  terminal_id?: number;
  from_date?: string;
  to_date?: string;
}) => apiClient.get<{ count: number }>('/v1/sync/transactions/count', { params });

// Get sync runs history
export const getSyncRuns = (limit?: number) =>
  apiClient.get<SyncRun[]>('/sync/runs', { params: { limit: limit || 20 } });

// Sync health check
export const checkSyncHealth = () =>
  apiClient.get<{ ok: boolean; status: string; status_code: number }>('/sync/health');

// Trigger sync with period
export const triggerSyncWithPeriod = (params: {
  period_start?: string;
  period_end?: string;
  items_per_page?: number;
  order_desc?: boolean;
}) => apiClient.post<{
  ok: boolean;
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  fetched: number;
  inserted: number;
  skipped_duplicates: number;
  expected_total: number;
  items_per_page: number;
  pages_fetched: number;
  last_page: number;
  transactions_synced: number;
  message: string;
}>('/sync/sync', null, { params });
