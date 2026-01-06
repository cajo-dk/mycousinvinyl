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
const manifestShortName = manifestEnv === 'nas' ? 'MCVinyl' : 'Vinyl-DEV'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      devOptions: {
        enabled: true,
      },
      includeAssets: [
        'icons/icon-192.png',
        'icons/icon-512.png',
      ],
      manifest: {
        name: 'MyCousinVinyl',
        short_name: manifestShortName,
        description: 'Personal vinyl collection manager',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#0b0f14',
        theme_color: '#0b0f14',
        icons: [
          {
            src: '/icons/icon-192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: '/icons/icon-512.png',
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
