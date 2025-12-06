import process from 'node:process';
import { test, expect, type Page, type Locator, type APIRequestContext } from '@playwright/test';
import { firstVisible } from './utils/login';
import { ROUTES, API_BASE_URL } from './constants';

async function navigateToAiBuildLab(page: Page, accessToken: string): Promise<boolean> {
  await page.addInitScript((token) => {
    window.localStorage.setItem('access_token', token as string);
    window.localStorage.setItem('refresh_token', token as string);
  }, accessToken);

  const targetUrl = ROUTES.composer ?? ROUTES.home;

  await page.goto(targetUrl);
  await page.waitForLoadState('networkidle');

  const urlAfter = page.url();
  console.log('[E2E] navigateToAiBuildLab: after goto, URL:', urlAfter);
  const htmlAfter = await page.content();
  console.log('[E2E] navigateToAiBuildLab: after goto, body snippet:', htmlAfter.slice(0, 1000));

  return true;
}

async function navigateToMyBuilds(page: Page): Promise<boolean> {
  if (ROUTES.export) {
    await page.goto(ROUTES.export);
    return true;
  }

  await page.goto(ROUTES.home);

  const candidates: Locator[] = [
    page.getByRole('link', { name: /mes builds/i }).first(),
    page.getByRole('button', { name: /mes builds/i }).first(),
  ];

  const target = await firstVisible(...candidates);
  if (!target) {
    return false;
  }

  await target.click();
  return true;
}

async function loginAndGetToken(request: APIRequestContext): Promise<string | null> {
  const email = process.env.E2E_USER;
  const password = process.env.E2E_PASS;

  if (!email || !password) {
    console.error('E2E_USER or E2E_PASS environment variables not set');
    return null;
  }

  try {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    formData.append('grant_type', 'password');

    const response = await request.post(`${API_BASE_URL}/auth/token`, {
      data: formData.toString(),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    if (!response.ok()) {
      const error = await response.text();
      console.error('Login failed:', error);
      return null;
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error('Error during login:', error);
    return null;
  }
}

// Reprend le même build Firebrand support que le test HPS
const FIREBRAND_SPEC_ID = 62;
const FIREBRAND_TRAITS = [2101];
const FIREBRAND_SKILLS = [9102, 43357];

async function runFirebrandAnalysis(page: Page) {
  const specInput = page.getByPlaceholder('ex: 62');
  const traitsInput = page.getByPlaceholder('ex: 2057, 2058, 2059');
  const skillsInput = page.getByPlaceholder('ex: 9153, 9154, 9155');
  const contextInput = page.getByPlaceholder('WvW Zerg, Roaming, PvE...');

  await specInput.fill(String(FIREBRAND_SPEC_ID));
  await traitsInput.fill(FIREBRAND_TRAITS.join(', '));
  await skillsInput.fill(FIREBRAND_SKILLS.join(', '));
  await contextInput.fill('WvW Zerg Firebrand support heal quickness stability');

  const analyzeButton = page.getByRole('button', { name: /analyser la synergie/i }).first();
  await analyzeButton.click();

  const resultContainer = page.getByText(/résultat/i).first();
  await expect(resultContainer).toBeVisible({ timeout: 30_000 });
}

test.describe('AI Build Lab - Firebrand Save to Mes Builds', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_BASE_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('should save Firebrand build and show it in Mes Builds', async ({ page }) => {
    test.setTimeout(120000);

    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    const accessToken = await loginAndGetToken(request);
    if (!accessToken) {
      test.fail(true, 'Failed to authenticate with the API');
      return;
    }

    const navigated = await navigateToAiBuildLab(page, accessToken);
    if (!navigated) {
      test.skip(true, 'AI Build Lab UI not exposed in current build');
      return;
    }

    const main = page.getByRole('main');
    await expect(main).toBeVisible({ timeout: 10_000 });

    await runFirebrandAnalysis(page);

    // Sauvegarder le build avec un nom unique
    const buildName = `Firebrand Support E2E ${Date.now()}`;

    page.once('dialog', async (dialog) => {
      await dialog.accept(buildName);
    });

    const saveButton = page.getByRole('button', { name: /sauvegarder ce build/i }).first();
    await saveButton.click();

    const toast = page.getByText(/build sauvegardé dans "?mes builds"?/i).first();
    await expect(toast).toBeVisible({ timeout: 10_000 });

    // Aller sur "Mes Builds" et vérifier la présence du build sauvegardé
    const goMyBuilds = await navigateToMyBuilds(page);
    if (!goMyBuilds) {
      test.skip(true, 'My Builds UI not exposed in current build');
      return;
    }

    const myBuildsMain = page.getByRole('main');
    await expect(myBuildsMain).toBeVisible({ timeout: 10_000 });

    const savedRow = page.getByText(buildName).first();
    await expect(savedRow).toBeVisible({ timeout: 30_000 });
  });
});
