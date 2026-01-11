/**
 * System logs API service (admin only).
 */

import { apiClient } from '../client';
import { PaginatedResponse, SystemLogEntry, LogRetentionResponse } from '@/types/api';

const BASE_URL = '/api/v1/admin';

export const systemLogsApi = {
  getLogs: async (params: { limit: number; offset: number }): Promise<PaginatedResponse<SystemLogEntry>> => {
    const response = await apiClient.get<PaginatedResponse<SystemLogEntry>>(`${BASE_URL}/logs`, { params });
    return response.data;
  },

  getLogRetention: async (): Promise<LogRetentionResponse> => {
    const response = await apiClient.get<LogRetentionResponse>(`${BASE_URL}/log-retention`);
    return response.data;
  },

  updateLogRetention: async (retention_days: number): Promise<LogRetentionResponse> => {
    const response = await apiClient.put<LogRetentionResponse>(`${BASE_URL}/log-retention`, { retention_days });
    return response.data;
  },
};
