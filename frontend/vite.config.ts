import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Dev: forward same-origin /api calls to the Django backend on the IPv4
      // loopback. changeOrigin rewrites the Host header (localhost:5173 ->
      // 127.0.0.1:8000) so Django's ALLOWED_HOSTS accepts the request. This
      // keeps development same-origin — no CORS and no IPv6/IPv4 localhost
      // resolution ambiguity.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})