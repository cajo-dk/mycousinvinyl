/**
 * Collection API service.
 */

import apiClient from '../client';
import type {
  CollectionItemResponse,
  CollectionItemCreate,
  CollectionItemUpdate,
  CollectionStatistics,
  PaginatedResponse,
  MessageResponse,
  Condition,
  CollectionItemDetailResponse,
  CollectionImportResponse,
  AlbumPlayIncrementResponse,
  PlayedAlbumEntry,
} from '@/types/api';

export const collectionApi = {
  /**
   * Add pressing to collection.
   */
  addItem: async (data: CollectionItemCreate): Promise<CollectionItemResponse> => {
    const response = await apiClient.post<CollectionItemResponse>('/api/v1/collection', data);
    return response.data;
  },

  /**
   * Get collection item by ID.
   */
  getById: async (id: string): Promise<CollectionItemResponse> => {
    const response = await apiClient.get<CollectionItemResponse>(`/api/v1/collection/${id}`);
    return response.data;
  },

  /**
   * Get user's collection with filters and search.
   */
  getCollection: async (params?: {
    query?: string;
    media_conditions?: Condition[];
    sleeve_conditions?: Condition[];
    rating_min?: number;
    rating_max?: number;
    sort_by?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<CollectionItemResponse>> => {
    const response = await apiClient.get<PaginatedResponse<CollectionItemResponse>>(
      '/api/v1/collection',
      { params }
    );
    return response.data;
  },

  /**
   * Get user's collection with artist and album details.
   * Returns data pre-sorted for hierarchical display.
   */
  getCollectionWithDetails: async (params?: {
    query?: string;
    sort_by?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<CollectionItemDetailResponse>> => {
    const response = await apiClient.get<PaginatedResponse<CollectionItemDetailResponse>>(
      '/api/v1/collection/with-details',
      { params }
    );
    return response.data;
  },

  /**
   * Update collection item.
   */
  update: async (id: string, data: CollectionItemUpdate): Promise<CollectionItemResponse> => {
    const response = await apiClient.put<CollectionItemResponse>(`/api/v1/collection/${id}`, data);
    return response.data;
  },

  /**
   * Update item condition.
   */
  updateCondition: async (
    id: string,
    data: {
      media_condition?: Condition;
      sleeve_condition?: Condition;
      defect_notes?: string;
    }
  ): Promise<CollectionItemResponse> => {
    const response = await apiClient.put<CollectionItemResponse>(
      `/api/v1/collection/${id}/condition`,
      data
    );
    return response.data;
  },

  /**
   * Update purchase information.
   */
  updatePurchaseInfo: async (
    id: string,
    data: {
      purchase_price?: number;
      purchase_currency?: string;
      purchase_date?: string;
      seller?: string;
    }
  ): Promise<CollectionItemResponse> => {
    const response = await apiClient.put<CollectionItemResponse>(
      `/api/v1/collection/${id}/purchase`,
      data
    );
    return response.data;
  },

  /**
   * Update item rating.
   */
  updateRating: async (
    id: string,
    data: {
      rating: number;
      notes?: string;
    }
  ): Promise<CollectionItemResponse> => {
    const response = await apiClient.put<CollectionItemResponse>(
      `/api/v1/collection/${id}/rating`,
      data
    );
    return response.data;
  },

  /**
   * Increment play count.
   */
  incrementPlayCount: async (id: string): Promise<CollectionItemResponse> => {
    const response = await apiClient.post<CollectionItemResponse>(
      `/api/v1/collection/${id}/play`
    );
    return response.data;
  },

  /**
   * Remove item from collection.
   */
  removeItem: async (id: string): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>(`/api/v1/collection/${id}`);
    return response.data;
  },

  /**
   * Get collection statistics.
   */
  getStatistics: async (): Promise<CollectionStatistics> => {
    const response = await apiClient.get<CollectionStatistics>('/api/v1/collection/statistics');
    return response.data;
  },

  /**
   * Increment album play count.
   */
  incrementAlbumPlayCount: async (albumId: string): Promise<AlbumPlayIncrementResponse> => {
    const response = await apiClient.post<AlbumPlayIncrementResponse>(
      `/api/v1/collection/albums/${albumId}/play`
    );
    return response.data;
  },

  /**
   * Get played albums for the year.
   */
  getPlayedAlbumsYtd: async (params?: {
    year?: number;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<PlayedAlbumEntry>> => {
    const response = await apiClient.get<PaginatedResponse<PlayedAlbumEntry>>(
      '/api/v1/collection/plays/ytd',
      { params }
    );
    return response.data;
  },

  /**
   * Import Discogs CSV collection export.
   */
  importDiscogs: async (file: File): Promise<CollectionImportResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<CollectionImportResponse>(
      '/api/v1/collection/imports/discogs',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  /**
   * Sync Discogs collection via API (PAT or OAuth).
   */
  syncDiscogs: async (): Promise<CollectionImportResponse> => {
    const response = await apiClient.post<CollectionImportResponse>(
      '/api/v1/collection/imports/discogs/sync'
    );
    return response.data;
  },

  /**
   * Get import status.
   */
  getImportStatus: async (importId: string): Promise<CollectionImportResponse> => {
    const response = await apiClient.get<CollectionImportResponse>(
      `/api/v1/collection/imports/${importId}`
    );
    return response.data;
  },
};
