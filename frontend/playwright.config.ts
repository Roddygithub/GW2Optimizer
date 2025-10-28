import process from 'node:process';
import { test as playwright } from '@playwright/test';

const { defineConfig, devices } = playwright;

const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:5173';
const isCI = Boolean(process.env.CI);

const config = defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: true,
  retries: isCI ? 2 : 0,
  workers: isCI ? 4 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
  ],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run preview -- --host',
    url: baseURL,
    reuseExistingServer: !isCI,
    timeout: 120_000,
  },
});

export default config;
