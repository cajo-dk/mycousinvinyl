/**
 * Azure Entra ID (Microsoft Authentication Library) configuration.
 *
 * This configures OAuth2 / OpenID Connect authentication with Azure.
 */

import { Configuration, PopupRequest } from '@azure/msal-browser';
import { getEnv } from '@/config/runtimeEnv';

const AZURE_CLIENT_ID = getEnv('VITE_AZURE_CLIENT_ID') || '';
const AZURE_TENANT_ID = getEnv('VITE_AZURE_TENANT_ID') || '';
const REDIRECT_URI = getEnv('VITE_AZURE_REDIRECT_URI') || window.location.origin;

/**
 * MSAL configuration object.
 * https://github.com/AzureAD/microsoft-authentication-library-for-js/blob/dev/lib/msal-browser/docs/configuration.md
 */
export const msalConfig: Configuration = {
  auth: {
    clientId: AZURE_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${AZURE_TENANT_ID}`,
    redirectUri: REDIRECT_URI,
    postLogoutRedirectUri: REDIRECT_URI,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

/**
 * Scopes for login request.
 * Requesting 'openid' and 'profile' to get user information.
 */
export const loginRequest: PopupRequest = {
  scopes: ['openid', 'profile', 'User.Read'],
};

/**
 * Scopes for API access token.
 * Update this with your backend API scope (e.g., 'api://your-api-id/access_as_user')
 */
export const apiRequest: PopupRequest = {
  scopes: [`api://${AZURE_CLIENT_ID}/access_as_user`],
};
