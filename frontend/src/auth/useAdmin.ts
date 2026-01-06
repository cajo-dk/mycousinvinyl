import { useEffect, useState } from 'react';
import { useMsal } from '@azure/msal-react';
import { apiRequest } from '@/auth/authConfig';
import apiClient from '@/api/client';
import { getEnv } from '@/config/runtimeEnv';

const ADMIN_GROUP_ID = getEnv('VITE_AZURE_GROUP_ADMIN') || '';
const DEBUG_ADMIN = getEnv('VITE_DEBUG_ADMIN') === 'true';

type Claims = {
  groups?: string[];
  roles?: string[];
};

type AdminState = {
  isAdmin: boolean;
  isLoading: boolean;
};

const decodeJwtClaims = (token: string): Claims | null => {
  const parts = token.split('.');
  if (parts.length < 2) {
    return null;
  }

  const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
  const padded = payload.padEnd(Math.ceil(payload.length / 4) * 4, '=');
  try {
    const json = atob(padded);
    return JSON.parse(json) as Claims;
  } catch {
    return null;
  }
};

const isAdminFromClaims = (claims?: Claims | null): boolean => {
  if (!claims) {
    return false;
  }
  if (ADMIN_GROUP_ID && Array.isArray(claims.groups) && claims.groups.includes(ADMIN_GROUP_ID)) {
    return true;
  }
  if (Array.isArray(claims.roles)) {
    return claims.roles.some((role) => role.toLowerCase() === 'admin');
  }
  return false;
};

const isAdminFromGroups = (groups?: string[] | null): boolean => {
  if (!ADMIN_GROUP_ID || !groups || !Array.isArray(groups)) {
    return false;
  }
  return groups.includes(ADMIN_GROUP_ID);
};

export function useIsAdmin(): AdminState {
  const { accounts, instance } = useMsal();
  const [state, setState] = useState<AdminState>({ isAdmin: false, isLoading: true });
  const claims = accounts[0]?.idTokenClaims as Claims | undefined;

  useEffect(() => {
    let isActive = true;

    const resolveAdmin = async () => {
      if (DEBUG_ADMIN) {
        if (isActive) setState({ isAdmin: true, isLoading: false });
        return;
      }

      if (!accounts[0]) {
        if (isActive) setState({ isAdmin: false, isLoading: false });
        return;
      }

      if (isAdminFromClaims(claims)) {
        if (isActive) setState({ isAdmin: true, isLoading: false });
        return;
      }

      try {
        const response = await instance.acquireTokenSilent({
          ...apiRequest,
          account: accounts[0],
        });
        const accessClaims = decodeJwtClaims(response.accessToken);
        const isAdmin = isAdminFromClaims(accessClaims);
        if (isActive) setState({ isAdmin, isLoading: false });
        if (isAdmin) {
          return;
        }
      } catch {
        // Fall through to API check below.
      }

      try {
        const response = await apiClient.get('/api/v1/me');
        const isAdmin = isAdminFromGroups(response.data?.groups);
        if (isActive) setState({ isAdmin, isLoading: false });
      } catch {
        if (isActive) setState({ isAdmin: false, isLoading: false });
      }
    };

    resolveAdmin();

    return () => {
      isActive = false;
    };
  }, [accounts, claims, instance]);

  return state;
}
