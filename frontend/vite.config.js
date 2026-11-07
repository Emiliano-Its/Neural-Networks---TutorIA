import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// El frontend llama a rutas relativas (/api/...) y Vite las reenvía a la API.
// Así no dependemos de CORS ni de si "localhost" resuelve a IPv4 o IPv6.
const API = process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true, // si 5173 está ocupado, falla con un mensaje claro en vez de usar otro puerto
    proxy: { '/api': { target: API, changeOrigin: true } },
  },
  preview: { port: 4173, proxy: { '/api': { target: API, changeOrigin: true } } },
})
