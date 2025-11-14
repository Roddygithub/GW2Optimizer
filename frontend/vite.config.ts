import { defineConfig } from 'vite';
import type { MinifyOptions } from 'terser';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'url';
import { visualizer } from 'rollup-plugin-visualizer';

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    mode === 'analyze' && visualizer({
      open: true,
      filename: 'bundle-analyzer-report.html',
      gzipSize: true,
      brotliSize: true,
    }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1'),
      },
    },
    port: 5174,
    strictPort: true,
    open: true,
  },
  preview: {
    port: 5174,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: mode !== 'production', // Désactive les sourcemaps en production
    chunkSizeWarningLimit: 1000, // Augmente la limite d'avertissement à 1000KB
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // React core (stable, rarely changes)
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react';
          }
          // Router (separate for code-splitting)
          if (id.includes('node_modules/react-router-dom')) {
            return 'router';
          }
          // UI libraries (heavy, separate chunk)
          if (id.includes('node_modules/framer-motion') || id.includes('node_modules/lucide-react')) {
            return 'ui';
          }
          // Zustand store (small, can be in vendor)
          if (id.includes('node_modules/zustand')) {
            return 'vendor';
          }
          // Axios and utilities
          if (id.includes('node_modules/axios') || 
              id.includes('node_modules/class-variance-authority') ||
              id.includes('node_modules/clsx') ||
              id.includes('node_modules/tailwind-merge')) {
            return 'vendor';
          }
          // Sentry (monitoring, separate)
          if (id.includes('node_modules/@sentry')) {
            return 'monitoring';
          }
          // All other node_modules
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
      },
    },
    // Activation de la compression
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production', // Supprime les console.log en production
      },
    } satisfies MinifyOptions,
    // Activation du chunking dynamique pour les imports asynchrones
    target: 'esnext',
    modulePreload: {
      polyfill: false, // Désactive le polyfill de préchargement des modules
    },
  },
}));
