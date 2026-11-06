import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Vite 配置文件
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    open: true,
    fs: {
      // 允许引用项目上级目录的资源
      allow: ['..'],
    },
    proxy: {
      // 代理 API 请求到后端服务
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      // 代理上传文件访问
      '/uploads': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
