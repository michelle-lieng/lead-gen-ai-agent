import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
  build: {
    rollupOptions: {
      output: {
        // Split heavy vendor libraries into their own chunks for better caching.
        manualChunks: {
          mui: ['@mui/material', '@mui/icons-material', '@mui/x-data-grid'],
          xlsx: ['xlsx'],
          vendor: ['react', 'react-dom', 'react-router-dom', '@tanstack/react-query', 'axios'],
        },
      },
    },
  },
});
