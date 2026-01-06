/**
 * Collection Sharing API service.
 */

import { apiClient } from '../client';
import {
  CollectionSharingSettings,
  FollowUserRequest,
  FollowsListResponse,
  UserSearchResponse,
  ItemOwnersResponse,
  PressingOwnersBatchResponse,
  AlbumOwnersBatchResponse
} from '@/types/api';

const BASE_URL = '/api/v1/collection-sharing';

export const collectionSharingApi = {
  /**
   * Get current user's collection sharing settings.
   */
  getSettings: async (): Promise<CollectionSharingSettings> => {
    const response = await apiClient.get<CollectionSharingSettings>(`${BASE_URL}/settings`);
    return response.data;
  },

  /**
   * Update collection sharing settings.
   */
  updateSettings: async (settings: Partial<CollectionSharingSettings>): Promise<CollectionSharingSettings> => {
    const response = await apiClient.put<CollectionSharingSettings>(`${BASE_URL}/settings`, settings);
    return response.data;
  },

  /**
   * Get list of users that the current user follows.
   */
  getFollows: async (): Promise<FollowsListResponse> => {
    const response = await apiClient.get<FollowsListResponse>(`${BASE_URL}/follows`);
    return response.data;
  },

  /**
   * Follow a user by user_id.
   */
  followUser: async (userId: string): Promise<void> => {
    const request: FollowUserRequest = { user_id: userId };
    await apiClient.post(`${BASE_URL}/follows`, request);
  },

  /**
   * Unfollow a user by user_id.
   */
  unfollowUser: async (userId: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/follows/${userId}`);
  },

  /**
   * Search users by name (autocomplete).
   */
  searchUsers: async (query: string, limit: number = 10): Promise<UserSearchResponse> => {
    const response = await apiClient.get<UserSearchResponse>(`${BASE_URL}/search`, {
      params: { query, limit }
    });
    return response.data;
  },

  /**
   * Get owners of a specific pressing (current user + followed users).
   */
  getPressingOwners: async (pressingId: string): Promise<ItemOwnersResponse> => {
    const response = await apiClient.get<ItemOwnersResponse>(
      `${BASE_URL}/owners/pressing/${pressingId}`
    );
    return response.data;
  },

  /**
   * Get owners of multiple pressings in a single request.
   */
  getPressingOwnersBatch: async (pressingIds: string[]): Promise<PressingOwnersBatchResponse> => {
    const response = await apiClient.post<PressingOwnersBatchResponse>(
      `${BASE_URL}/owners/pressings`,
      { pressing_ids: pressingIds }
    );
    return response.data;
  },

  /**
   * Get owners of a specific album (current user + followed users).
   */
  getAlbumOwners: async (albumId: string): Promise<ItemOwnersResponse> => {
    const response = await apiClient.get<ItemOwnersResponse>(
      `${BASE_URL}/owners/album/${albumId}`
    );
    return response.data;
  },

  /**
   * Get owners of multiple albums in a single request.
   */
  getAlbumOwnersBatch: async (albumIds: string[]): Promise<AlbumOwnersBatchResponse> => {
    const response = await apiClient.post<AlbumOwnersBatchResponse>(
      `${BASE_URL}/owners/albums`,
      { album_ids: albumIds }
    );
    return response.data;
  },
};
