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
        // The UI is built from this project's own components, so there is no
        // component-library chunk; xlsx is the only heavy leaf dependency, and
        // it is only pulled in when someone opens the import sheet.
        manualChunks: {
          xlsx: ['xlsx'],
          vendor: ['react', 'react-dom', 'react-router-dom', '@tanstack/react-query', 'axios'],
        },
      },
    },
  },
});
