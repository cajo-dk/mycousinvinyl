type RuntimeEnv = Partial<ImportMetaEnv> & {
  VITE_AZURE_GROUP_ADMIN?: string;
  VITE_DEBUG_ADMIN?: string;
  VITE_DEBUG_NAV?: string;
};

const runtimeEnv = (window.__ENV || {}) as RuntimeEnv;

export const getEnv = (key: keyof RuntimeEnv): string => {
  const value = runtimeEnv[key];
  if (value !== undefined && value !== null && value !== '') {
    return String(value);
  }

  const metaEnv = import.meta.env as unknown as RuntimeEnv;
  return String(metaEnv[key] ?? '');
};
