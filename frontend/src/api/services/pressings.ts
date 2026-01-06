/**
 * Pressing API service.
 */

import apiClient from '../client';
import type {
  PressingResponse,
  PressingCreate,
  PressingUpdate,
  PressingDetailResponse,
  PackagingResponse,
  PackagingCreateOrUpdate,
  PaginatedResponse,
  MessageResponse,
} from '@/types/api';

export const pressingsApi = {
  /**
   * Create a new pressing.
   */
  create: async (data: PressingCreate): Promise<PressingResponse> => {
    const response = await apiClient.post<PressingResponse>('/api/v1/pressings', data);
    return response.data;
  },

  /**
   * Get pressing by ID.
   */
  getById: async (id: string): Promise<PressingResponse> => {
    const response = await apiClient.get<PressingResponse>(`/api/v1/pressings/${id}`);
    return response.data;
  },

  /**
   * Get pressings for an album.
   */
  getByAlbum: async (albumId: string, params?: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<PressingResponse>> => {
    const response = await apiClient.get<PaginatedResponse<PressingResponse>>(
      `/api/v1/pressings/album/${albumId}`,
      { params }
    );
    return response.data;
  },

  /**
   * Search pressings with filters.
   */
  search: async (params?: {
    format?: string;
    speed?: string;
    size?: string;
    country?: string;
    year_min?: number;
    year_max?: number;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<PressingResponse>> => {
    const response = await apiClient.get<PaginatedResponse<PressingResponse>>(
      '/api/v1/pressings',
      { params }
    );
    return response.data;
  },

  /**
   * Update a pressing.
   */
  update: async (id: string, data: PressingUpdate): Promise<PressingResponse> => {
    const response = await apiClient.put<PressingResponse>(`/api/v1/pressings/${id}`, data);
    return response.data;
  },

  /**
   * Delete a pressing.
   */
  delete: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/pressings/${id}`);
    return response.data;
  },

  /**
   * Get pressings with artist and album details for hierarchical display.
   */
  getPressingsWithDetails: async (params?: {
    query?: string;
    artist_id?: string;
    album_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<PressingDetailResponse>> => {
    const response = await apiClient.get<PaginatedResponse<PressingDetailResponse>>(
      '/api/v1/pressings/with-details',
      { params }
    );
    return response.data;
  },

  /**
   * Get packaging details for a pressing.
   */
  getPackaging: async (id: string): Promise<PackagingResponse | null> => {
    try {
      const response = await apiClient.get<PackagingResponse>(`/api/v1/pressings/${id}/packaging`);
      return response.data;
    } catch (error: any) {
      if (error?.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  /**
   * Add or update packaging details for a pressing.
   */
  upsertPackaging: async (id: string, data: PackagingCreateOrUpdate): Promise<PackagingResponse> => {
    const response = await apiClient.put<PackagingResponse>(`/api/v1/pressings/${id}/packaging`, data);
    return response.data;
  },
};
