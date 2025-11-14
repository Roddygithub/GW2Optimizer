import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    exclude: [
      'tests/e2e/**',
      '**/node_modules/**',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'json-summary'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'tests/e2e/**',
        '**/*.stories.*',
        '**/__mocks__/**',
        '**/fixtures/**',
        '**/*.d.ts',
        '**/types/**',
        '**/generated/**',
        'node_modules/',
        'dist/',
        // Exclude trivial navigation helpers from coverage to avoid skewing function coverage
        'src/lib/navigation/**',
        'src/lib/navigation.ts',
      ],
      thresholds: {
        lines: 49,
        statements: 49,
        functions: 61,
        branches: 70,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
