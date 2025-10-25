import { defineConfig } from 'vite';
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
        manualChunks: {
          // Regroupement des dépendances principales
          react: ['react', 'react-dom', 'react-router-dom'],
          vendor: ['axios', 'class-variance-authority', 'clsx', 'tailwind-merge'],
          // Regroupement des dépendances UI
          ui: ['framer-motion', 'lucide-react'],
          // Séparation des dépendances de développement
          ...(mode === 'development' ? {
            dev: ['@testing-library/react', '@testing-library/user-event', '@testing-library/jest-dom'],
          } : {}),
        },
      },
    },
    // Activation de la compression
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production', // Supprime les console.log en production
      },
    } as any,
    // Activation du chunking dynamique pour les imports asynchrones
    target: 'esnext',
    modulePreload: {
      polyfill: false, // Désactive le polyfill de préchargement des modules
    },
  },
}));
