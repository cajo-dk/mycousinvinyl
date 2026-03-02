/**
 * Admin tools API service.
 */

import { apiClient } from '../client';
import { DatabaseCliExecuteRequest, DatabaseCliExecuteResponse, MessageResponse } from '@/types/api';

const BASE_URL = '/api/v1/admin/tools';

export const toolsApi = {
  runBackup: async (): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(`${BASE_URL}/backup`);
    return response.data;
  },
  runTracklistSync: async (): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>(`${BASE_URL}/tracklist-sync`);
    return response.data;
  },
  executeDatabaseCli: async (payload: DatabaseCliExecuteRequest): Promise<DatabaseCliExecuteResponse> => {
    const response = await apiClient.post<DatabaseCliExecuteResponse>(`${BASE_URL}/database-cli/execute`, payload);
    return response.data;
  },
};
