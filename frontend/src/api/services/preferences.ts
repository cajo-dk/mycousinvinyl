/**
 * Preferences API service.
 */

import { apiClient } from '../client';
import { PreferencesResponse } from '@/types/api';

const BASE_URL = '/api/v1/preferences';

export const preferencesApi = {
  /**
   * Get current user preferences.
   */
  getPreferences: async (): Promise<PreferencesResponse> => {
    const response = await apiClient.get<PreferencesResponse>(BASE_URL);
    return response.data;
  },

  /**
   * Update preferred currency (ISO 4217).
   */
  updateCurrency: async (currency: string): Promise<PreferencesResponse> => {
    const response = await apiClient.put<PreferencesResponse>(`${BASE_URL}/currency`, { currency });
    return response.data;
  },

  /**
   * Update display settings.
   */
  updateDisplaySettings: async (display_settings: Record<string, any>): Promise<PreferencesResponse> => {
    const response = await apiClient.put<PreferencesResponse>(`${BASE_URL}/display`, { display_settings });
    return response.data;
  },
};
