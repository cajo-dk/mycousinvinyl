import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import fs from 'fs'
import path from 'path'

const certsDir = path.resolve(__dirname, 'certs')
const wildcardPfxPath = path.join(certsDir, 'cajo.dk.p12')
const fallbackPfxPath = path.join(certsDir, 'mcvinyl-dev.pfx')
const selectedPfxPath = fs.existsSync(wildcardPfxPath)
  ? wildcardPfxPath
  : fs.existsSync(fallbackPfxPath)
    ? fallbackPfxPath
    : null

const isWildcard = selectedPfxPath === wildcardPfxPath
const passphrase =
  process.env.VITE_HTTPS_PASSPHRASE ||
  process.env.HTTPS_PASSPHRASE ||
  (isWildcard ? undefined : 'mcvinyl-dev')

const httpsConfig = selectedPfxPath
  ? {
      pfx: fs.readFileSync(selectedPfxPath),
      passphrase,
    }
  : undefined

const manifestEnv = (process.env.VITE_MANIFEST_ENV || 'local').toLowerCase()
const isHaAddon = manifestEnv === 'nas'
const manifestShortName = isHaAddon ? 'MCVinyl' : 'MCV-DEV'
const manifestIcon192 = isHaAddon ? '/icons/icon-192-ha.png' : '/icons/icon-192-dev.png'
const manifestIcon512 = isHaAddon ? '/icons/icon-512-ha.png' : '/icons/icon-512-dev.png'
const manifestBackgroundColor = isHaAddon ? '#000000' : '#1d4ed8'
const manifestThemeColor = manifestBackgroundColor
const manifestIncludeAssets = isHaAddon
  ? ['icons/icon-192-ha.png', 'icons/icon-512-ha.png']
  : ['icons/icon-192-dev.png', 'icons/icon-512-dev.png']

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      devOptions: {
        enabled: true,
      },
      includeAssets: manifestIncludeAssets,
      manifest: {
        name: 'MyCousinVinyl',
        short_name: manifestShortName,
        description: 'Personal vinyl collection manager',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: manifestBackgroundColor,
        theme_color: manifestThemeColor,
        icons: [
          {
            src: manifestIcon192,
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: manifestIcon512,
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 6 * 1024 * 1024,
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    https: httpsConfig,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  preview: {
    host: true,
    https: httpsConfig,
  },
})
