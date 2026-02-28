/**
 * Admin tools API service.
 */

import { apiClient } from '../client';
import { MessageResponse } from '@/types/api';

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
};
