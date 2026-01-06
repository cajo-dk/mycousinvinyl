/**
 * Album API service.
 */

import apiClient from '../client';
import type {
  AlbumResponse,
  AlbumCreate,
  AlbumUpdate,
  AlbumDetailResponse,
  PaginatedResponse,
  MessageResponse,
} from '@/types/api';

export const albumsApi = {
  buildParams: (params?: {
    query?: string;
    artist_id?: string;
    genre_ids?: string[];
    style_ids?: string[];
    release_type?: string;
    year_min?: number;
    year_max?: number;
    sort_by?: string;
    limit?: number;
    offset?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (!params) {
      return searchParams;
    }

    if (params.query) searchParams.set('query', params.query);
    if (params.artist_id) searchParams.set('artist_id', params.artist_id);
    if (params.release_type) searchParams.set('release_type', params.release_type);
    if (params.year_min !== undefined) searchParams.set('year_min', String(params.year_min));
    if (params.year_max !== undefined) searchParams.set('year_max', String(params.year_max));
    if (params.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params.limit !== undefined) searchParams.set('limit', String(params.limit));
    if (params.offset !== undefined) searchParams.set('offset', String(params.offset));

    if (params.genre_ids?.length) {
      params.genre_ids.forEach((id) => searchParams.append('genre_ids', id));
    }
    if (params.style_ids?.length) {
      params.style_ids.forEach((id) => searchParams.append('style_ids', id));
    }

    return searchParams;
  },
  /**
   * Create a new album.
   */
  create: async (data: AlbumCreate): Promise<AlbumResponse> => {
    const response = await apiClient.post<AlbumResponse>('/api/v1/albums', data);
    return response.data;
  },

  /**
   * Get album by ID.
   */
  getById: async (id: string): Promise<AlbumResponse> => {
    const response = await apiClient.get<AlbumResponse>(`/api/v1/albums/${id}`);
    return response.data;
  },

  /**
   * Search albums with full-text search and filters.
   */
  search: async (params?: {
    query?: string;
    artist_id?: string;
    genre_ids?: string[];
    style_ids?: string[];
    release_type?: string;
    year_min?: number;
    year_max?: number;
    sort_by?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<AlbumResponse>> => {
    const response = await apiClient.get<PaginatedResponse<AlbumResponse>>(
      '/api/v1/albums',
      { params: albumsApi.buildParams(params) }
    );
    return response.data;
  },

  /**
   * Get albums by artist.
   */
  getByArtist: async (artistId: string, params?: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<AlbumResponse>> => {
    const response = await apiClient.get<PaginatedResponse<AlbumResponse>>(
      `/api/v1/albums/artist/${artistId}`,
      { params }
    );
    return response.data;
  },

  /**
   * Update an album.
   */
  update: async (id: string, data: AlbumUpdate): Promise<AlbumResponse> => {
    const response = await apiClient.put<AlbumResponse>(`/api/v1/albums/${id}`, data);
    return response.data;
  },

  /**
   * Delete an album.
   */
  delete: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/albums/${id}`);
    return response.data;
  },

  /**
   * Get albums with artist details and pressing counts for hierarchical display.
   */
  getAlbumsWithDetails: async (params?: {
    query?: string;
    artist_id?: string;
    genre_ids?: string[];
    style_ids?: string[];
    release_type?: string;
    year_min?: number;
    year_max?: number;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<AlbumDetailResponse>> => {
    const response = await apiClient.get<PaginatedResponse<AlbumDetailResponse>>(
      '/api/v1/albums/with-details',
      { params: albumsApi.buildParams(params) }
    );
    return response.data;
  },
};
