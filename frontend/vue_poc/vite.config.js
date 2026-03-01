import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/vue_poc/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  }
})
