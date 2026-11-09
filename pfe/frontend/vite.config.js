import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API to backend so browser sends same-origin requests and Authorization header is never stripped by CORS
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});

