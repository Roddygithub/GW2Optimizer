import process from 'node:process';
import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.E2E_BASE_URL ?? 'http://localhost:5173';
const isCI = Boolean(process.env.CI);

// En mode Docker/CI avec E2E_BASE_URL défini, on cible un frontend déjà démarré
// (par ex. Nginx sur host.docker.internal:80) et on évite de lancer Vite/preview
// dans le conteneur Playwright, ce qui contourne la contrainte de version Node.
const webServer = process.env.E2E_BASE_URL
  ? undefined
  : {
      command: 'npm run build && npm run preview -- --host --port 5173',
      url: baseURL,
      reuseExistingServer: !isCI,
      timeout: 120_000,
    };

export default defineConfig({
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
    ['json', { outputFile: 'playwright-report/report.json' }],
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
  webServer,
});
