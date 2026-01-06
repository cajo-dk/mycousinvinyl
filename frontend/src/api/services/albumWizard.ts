/**
 * Album Wizard API service.
 */

import { apiClient } from '../client';
import { AlbumWizardScanRequest, AlbumWizardScanResponse } from '@/types/api';

const BASE_URL = '/api/v1/album-wizard';

export const albumWizardApi = {
  scanAlbum: async (imageDataUrl: string): Promise<AlbumWizardScanResponse> => {
    const payload: AlbumWizardScanRequest = { image_data_url: imageDataUrl };
    const response = await apiClient.post<AlbumWizardScanResponse>(`${BASE_URL}/scan`, payload);
    return response.data;
  },
};
