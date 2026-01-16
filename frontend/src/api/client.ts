/**
 * API client with automatic Azure Entra ID token injection.
 */

import axios from 'axios';
import { apiRequest } from '@/auth/authConfig';
import { getEnv } from '@/config/runtimeEnv';

const API_BASE_URL = getEnv('VITE_API_URL') || '';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Store MSAL instance (will be set by configureMsalInstance)
let msalInstanceRef: any = null;

async function clearMsalSession() {
  if (!msalInstanceRef) {
    return;
  }

  const account = msalInstanceRef.getActiveAccount?.() || msalInstanceRef.getAllAccounts?.()[0];
  const tokenCache = msalInstanceRef.getTokenCache?.();

  if (account && tokenCache?.removeAccount) {
    try {
      await tokenCache.removeAccount(account);
    } catch (cacheError) {
      console.error('Failed to clear MSAL cache:', cacheError);
    }
  }

  msalInstanceRef.setActiveAccount?.(null);
}

/**
 * Configure the API client with an initialized MSAL instance.
 * This must be called after MSAL is initialized in main.tsx
 */
export function configureMsalInstance(instance: any) {
  msalInstanceRef = instance;
}

/**
 * Request interceptor to add access token to requests.
 */
apiClient.interceptors.request.use(
  async (config) => {
    try {
      if (!msalInstanceRef) {
        console.warn('MSAL instance not configured');
        return config;
      }

      const accounts = msalInstanceRef.getAllAccounts();
      if (accounts.length === 0) {
        throw new Error('No active account');
      }

      const account = accounts[0];

      let response;
      try {
        // Try to acquire token silently first
        response = await msalInstanceRef.acquireTokenSilent({
          ...apiRequest,
          account,
        });
      } catch (silentError: any) {
        console.log('Silent token acquisition failed, trying popup...', silentError);

        // If silent acquisition fails (e.g., consent required), use popup
        if (silentError.errorCode === 'consent_required' ||
            silentError.errorCode === 'interaction_required' ||
            silentError.errorCode === 'login_required') {
          try {
            response = await msalInstanceRef.acquireTokenPopup({
              ...apiRequest,
              account,
            });
          } catch (popupError) {
            console.error('Popup token acquisition failed:', popupError);
            throw popupError;
          }
        } else {
          throw silentError;
        }
      }

      // Add token to Authorization header
      if (response && response.accessToken) {
        config.headers.Authorization = `Bearer ${response.accessToken}`;
      }
    } catch (error: any) {
      if (error?.errorCode === 'interaction_required' || error?.errorCode === 'login_required') {
        await clearMsalSession();
      }
      console.error('Error acquiring token:', error);
      // Token acquisition failed - request will proceed without auth header
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling.
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - show login view
      console.error('Unauthorized - token may be expired');
      await clearMsalSession();
    }

    if (error.response?.status === 403) {
      // User lacks required permissions
      console.error('Forbidden - insufficient permissions');
      // Enhance error message for user
      error.message = 'You do not have permission to perform this action. Contact your administrator for access.';
    }

    return Promise.reject(error);
  }
);

export default apiClient;
