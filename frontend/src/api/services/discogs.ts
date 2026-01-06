/**
 * Discogs API service (via backend proxy).
 */

import apiClient from '../client';
import type {
  DiscogsArtistSearchResponse,
  DiscogsArtistDetails,
  DiscogsAlbumSearchResponse,
  DiscogsAlbumDetails,
  DiscogsReleaseSearchResponse,
  DiscogsReleaseDetails,
  DiscogsOAuthStartRequest,
  DiscogsOAuthStartResponse,
  DiscogsOAuthStatusResponse,
  DiscogsPatConnectRequest,
  MessageResponse,
} from '@/types/api';

export const discogsApi = {
  searchArtists: async (query: string, limit = 3): Promise<DiscogsArtistSearchResponse> => {
    const response = await apiClient.get<DiscogsArtistSearchResponse>(
      '/api/v1/discogs/artists/search',
      { params: { query, limit } }
    );
    return response.data;
  },

  getArtist: async (artistId: number): Promise<DiscogsArtistDetails> => {
    const response = await apiClient.get<DiscogsArtistDetails>(
      `/api/v1/discogs/artists/${artistId}`
    );
    return response.data;
  },

  searchAlbums: async (artistId: number, query: string, limit = 10, page = 1): Promise<DiscogsAlbumSearchResponse> => {
    const response = await apiClient.get<DiscogsAlbumSearchResponse>(
      '/api/v1/discogs/albums/search',
      { params: { artist_id: artistId, query, limit, page } }
    );
    return response.data;
  },

  getAlbum: async (albumId: number, albumType?: string): Promise<DiscogsAlbumDetails> => {
    const response = await apiClient.get<DiscogsAlbumDetails>(
      `/api/v1/discogs/albums/${albumId}`,
      { params: albumType ? { type: albumType } : {} }
    );
    return response.data;
  },

  getMasterReleases: async (masterId: number, page = 1, limit = 25): Promise<DiscogsReleaseSearchResponse> => {
    const response = await apiClient.get<DiscogsReleaseSearchResponse>(
      `/api/v1/discogs/masters/${masterId}/releases`,
      { params: { page, limit } }
    );
    return response.data;
  },

  searchMasterReleases: async (
    masterId: number,
    query: string,
    limit = 25
  ): Promise<DiscogsReleaseSearchResponse> => {
    const response = await apiClient.get<DiscogsReleaseSearchResponse>(
      `/api/v1/discogs/masters/${masterId}/search`,
      { params: { q: query, limit } }
    );
    return response.data;
  },

  getRelease: async (releaseId: number): Promise<DiscogsReleaseDetails> => {
    const response = await apiClient.get<DiscogsReleaseDetails>(
      `/api/v1/discogs/releases/${releaseId}`
    );
    return response.data;
  },

  getAlbumReleases: async (albumId: string, page = 1, limit = 25): Promise<DiscogsReleaseSearchResponse> => {
    const response = await apiClient.get<DiscogsReleaseSearchResponse>(
      `/api/v1/discogs/albums/${albumId}/releases`,
      { params: { page, limit } }
    );
    return response.data;
  },

  getOAuthStatus: async (): Promise<DiscogsOAuthStatusResponse> => {
    const response = await apiClient.get<DiscogsOAuthStatusResponse>('/api/v1/discogs/oauth/status');
    return response.data;
  },

  startOAuth: async (payload: DiscogsOAuthStartRequest): Promise<DiscogsOAuthStartResponse> => {
    const response = await apiClient.post<DiscogsOAuthStartResponse>(
      '/api/v1/discogs/oauth/start',
      payload
    );
    return response.data;
  },

  disconnectOAuth: async (): Promise<MessageResponse> => {
    const response = await apiClient.delete<MessageResponse>('/api/v1/discogs/oauth/disconnect');
    return response.data;
  },

  connectPat: async (payload: DiscogsPatConnectRequest): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>('/api/v1/discogs/pat', payload);
    return response.data;
  },
};
