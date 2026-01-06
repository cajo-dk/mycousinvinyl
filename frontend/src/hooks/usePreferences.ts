import { useCallback, useEffect, useState } from 'react';
import { preferencesApi } from '@/api/services';
import { PreferencesResponse } from '@/types/api';

export function usePreferences() {
  const [preferences, setPreferences] = useState<PreferencesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await preferencesApi.getPreferences();
      setPreferences(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load preferences');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { preferences, loading, error, refresh };
}
