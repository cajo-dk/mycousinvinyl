/**
 * Artist API service.
 */

import apiClient from '../client';
import type {
  ArtistResponse,
  ArtistCreate,
  ArtistUpdate,
  PaginatedResponse,
  MessageResponse,
} from '@/types/api';

export const artistsApi = {
  /**
   * Create a new artist.
   */
  create: async (data: ArtistCreate): Promise<ArtistResponse> => {
    const response = await apiClient.post<ArtistResponse>('/api/v1/artists', data);
    return response.data;
  },

  /**
   * Get artist by ID.
   */
  getById: async (id: string): Promise<ArtistResponse> => {
    const response = await apiClient.get<ArtistResponse>(`/api/v1/artists/${id}`);
    return response.data;
  },

  /**
   * Search artists with optional filters.
   */
  search: async (params?: {
    query?: string;
    artist_type?: string;
    country?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<ArtistResponse>> => {
    const response = await apiClient.get<PaginatedResponse<ArtistResponse>>(
      '/api/v1/artists',
      { params }
    );
    return response.data;
  },

  /**
   * Update an artist.
   */
  update: async (id: string, data: ArtistUpdate): Promise<ArtistResponse> => {
    const response = await apiClient.put<ArtistResponse>(`/api/v1/artists/${id}`, data);
    return response.data;
  },

  /**
   * Delete an artist.
   */
  delete: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/artists/${id}`);
    return response.data;
  },
};
