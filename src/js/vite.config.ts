import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import path from 'path'

const APP_URL = process.env.APP_URL || "http://localhost:8080"
const API_URL = APP_URL
const ASSET_URL = process.env.ASSET_URL || "/"
const VITE_PORT = process.env.VITE_PORT || "5173"
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), TanStackRouterVite()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: +`${VITE_PORT}`,
    host: "0.0.0.0",
    cors: true,
    proxy: {
      '/api': {
        target: API_URL,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../py/app/server/web/static',
    emptyOutDir: true,
  },
})
