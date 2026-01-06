/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_AZURE_CLIENT_ID: string
  readonly VITE_AZURE_TENANT_ID: string
  readonly VITE_AZURE_REDIRECT_URI: string
  readonly VITE_AZURE_GROUP_ADMIN?: string
  readonly VITE_DEBUG_ADMIN?: string
  readonly VITE_DEBUG_NAV?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface Window {
  __ENV?: Partial<ImportMetaEnv> & {
    VITE_AZURE_GROUP_ADMIN?: string
    VITE_DEBUG_ADMIN?: string
    VITE_DEBUG_NAV?: string
  }
}
