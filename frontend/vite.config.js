import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 開發時：npm run dev（:5173），/api 與 /assets 轉給本機 Flask（:5000）
// 正式時：npm run build → dist/，由 Flask 直接提供
const FLASK_URL = process.env.NOTEADVENTURE_FLASK_URL || 'http://127.0.0.1:5000'

export default defineConfig({
  // /assets/material/... 由 Flask 提供，不要讓 Vite 當成模組打包
  plugins: [vue({ template: { transformAssetUrls: { includeAbsolute: false } } })],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': FLASK_URL,
      '/assets/material': FLASK_URL
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
