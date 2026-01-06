/**
 * Lookup API service - genres, styles, countries.
 */

import { apiClient } from '../client';
import {
  GenreResponse,
  StyleResponse,
  CountryResponse,
  ArtistTypeResponse,
  ReleaseTypeResponse,
  EditionTypeResponse,
  SleeveTypeResponse,
} from '@/types/api';

const BASE_URL = '/api/v1/lookup';

export const lookupApi = {
  /**
   * Get all genres.
   */
  getAllGenres: async (): Promise<GenreResponse[]> => {
    const response = await apiClient.get<GenreResponse[]>(`${BASE_URL}/genres`);
    return response.data;
  },

  createGenre: async (data: {
    name: string;
    display_order?: number;
  }): Promise<GenreResponse> => {
    const response = await apiClient.post<GenreResponse>(`${BASE_URL}/genres`, data);
    return response.data;
  },

  updateGenre: async (genreId: string, data: {
    name: string;
    display_order?: number;
  }): Promise<GenreResponse> => {
    const response = await apiClient.put<GenreResponse>(`${BASE_URL}/genres/${genreId}`, data);
    return response.data;
  },

  deleteGenre: async (genreId: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/genres/${genreId}`);
  },

  /**
   * Get genre by ID.
   */
  getGenre: async (genreId: string): Promise<GenreResponse> => {
    const response = await apiClient.get<GenreResponse>(`${BASE_URL}/genres/${genreId}`);
    return response.data;
  },

  /**
   * Get all styles, optionally filtered by genre.
   */
  getAllStyles: async (genreId?: string): Promise<StyleResponse[]> => {
    const response = await apiClient.get<StyleResponse[]>(`${BASE_URL}/styles`, {
      params: genreId ? { genre_id: genreId } : {},
    });
    return response.data;
  },

  createStyle: async (data: {
    name: string;
    genre_id?: string;
    display_order?: number;
  }): Promise<StyleResponse> => {
    const response = await apiClient.post<StyleResponse>(`${BASE_URL}/styles`, data);
    return response.data;
  },

  updateStyle: async (styleId: string, data: {
    name: string;
    genre_id?: string;
    display_order?: number;
  }): Promise<StyleResponse> => {
    const response = await apiClient.put<StyleResponse>(`${BASE_URL}/styles/${styleId}`, data);
    return response.data;
  },

  deleteStyle: async (styleId: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/styles/${styleId}`);
  },

  /**
   * Get style by ID.
   */
  getStyle: async (styleId: string): Promise<StyleResponse> => {
    const response = await apiClient.get<StyleResponse>(`${BASE_URL}/styles/${styleId}`);
    return response.data;
  },

  /**
   * Get all countries.
   */
  getAllCountries: async (): Promise<CountryResponse[]> => {
    const response = await apiClient.get<CountryResponse[]>(`${BASE_URL}/countries`);
    return response.data;
  },

  /**
   * Get country by code.
   */
  getCountry: async (code: string): Promise<CountryResponse> => {
    const response = await apiClient.get<CountryResponse>(`${BASE_URL}/countries/${code}`);
    return response.data;
  },

  /**
   * Get all artist types.
   */
  getAllArtistTypes: async (): Promise<ArtistTypeResponse[]> => {
    const response = await apiClient.get<ArtistTypeResponse[]>(`${BASE_URL}/artist-types`);
    return response.data;
  },

  createArtistType: async (data: {
    code: string;
    name: string;
    display_order?: number;
  }): Promise<ArtistTypeResponse> => {
    const response = await apiClient.post<ArtistTypeResponse>(`${BASE_URL}/artist-types`, data);
    return response.data;
  },

  updateArtistType: async (code: string, data: {
    name: string;
    display_order?: number;
  }): Promise<ArtistTypeResponse> => {
    const response = await apiClient.put<ArtistTypeResponse>(`${BASE_URL}/artist-types/${code}`, data);
    return response.data;
  },

  deleteArtistType: async (code: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/artist-types/${code}`);
  },

  /**
   * Get all release types.
   */
  getAllReleaseTypes: async (): Promise<ReleaseTypeResponse[]> => {
    const response = await apiClient.get<ReleaseTypeResponse[]>(`${BASE_URL}/release-types`);
    return response.data;
  },

  createReleaseType: async (data: {
    code: string;
    name: string;
    display_order?: number;
  }): Promise<ReleaseTypeResponse> => {
    const response = await apiClient.post<ReleaseTypeResponse>(`${BASE_URL}/release-types`, data);
    return response.data;
  },

  updateReleaseType: async (code: string, data: {
    name: string;
    display_order?: number;
  }): Promise<ReleaseTypeResponse> => {
    const response = await apiClient.put<ReleaseTypeResponse>(`${BASE_URL}/release-types/${code}`, data);
    return response.data;
  },

  deleteReleaseType: async (code: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/release-types/${code}`);
  },

  /**
   * Get all edition types.
   */
  getAllEditionTypes: async (): Promise<EditionTypeResponse[]> => {
    const response = await apiClient.get<EditionTypeResponse[]>(`${BASE_URL}/edition-types`);
    return response.data;
  },

  createEditionType: async (data: {
    code: string;
    name: string;
    display_order?: number;
  }): Promise<EditionTypeResponse> => {
    const response = await apiClient.post<EditionTypeResponse>(`${BASE_URL}/edition-types`, data);
    return response.data;
  },

  updateEditionType: async (code: string, data: {
    name: string;
    display_order?: number;
  }): Promise<EditionTypeResponse> => {
    const response = await apiClient.put<EditionTypeResponse>(`${BASE_URL}/edition-types/${code}`, data);
    return response.data;
  },

  deleteEditionType: async (code: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/edition-types/${code}`);
  },

  /**
   * Get all sleeve types.
   */
  getAllSleeveTypes: async (): Promise<SleeveTypeResponse[]> => {
    const response = await apiClient.get<SleeveTypeResponse[]>(`${BASE_URL}/sleeve-types`);
    return response.data;
  },

  createSleeveType: async (data: {
    code: string;
    name: string;
    display_order?: number;
  }): Promise<SleeveTypeResponse> => {
    const response = await apiClient.post<SleeveTypeResponse>(`${BASE_URL}/sleeve-types`, data);
    return response.data;
  },

  updateSleeveType: async (code: string, data: {
    name: string;
    display_order?: number;
  }): Promise<SleeveTypeResponse> => {
    const response = await apiClient.put<SleeveTypeResponse>(`${BASE_URL}/sleeve-types/${code}`, data);
    return response.data;
  },

  deleteSleeveType: async (code: string): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/sleeve-types/${code}`);
  },
};
