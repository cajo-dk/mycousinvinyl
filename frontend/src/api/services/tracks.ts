/**
 * Track API service.
 */

import apiClient from '../client';
import type { TrackResponse } from '@/types/api';

export const tracksApi = {
  /**
   * Get all tracks for an album.
   */
  getByAlbum: async (albumId: string): Promise<TrackResponse[]> => {
    const response = await apiClient.get<TrackResponse[]>(`/api/v1/tracks/album/${albumId}`);
    return response.data;
  },
};

