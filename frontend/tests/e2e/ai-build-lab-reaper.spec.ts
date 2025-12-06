import process from 'node:process';
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
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

// Reaper DPS build (IDs depuis les dumps locaux):
// - Spécialisation Reaper: id = 34 (Necromancer elite spec)
// - Quelques traits de la ligne Reaper: 1974, 2020, 2026
// - Skill de burst emblématique: Gravedigger (id = 30142)

const REAPER_SPEC_ID = 34;
const REAPER_TRAITS = [1974, 2020, 2026];
const REAPER_SKILLS = [30142];

test.describe('AI Build Lab - Reaper DPS & Meta', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    request = await playwright.request.newContext({
      baseURL: API_BASE_URL,
    });
  });

  test.afterAll(async () => {
    await request.dispose();
  });

  test('should compute DPS and show meta comparison for Reaper power DPS WvW', async ({ page }) => {
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

    const specInput = page.getByPlaceholder('ex: 62');
    const traitsInput = page.getByPlaceholder('ex: 2057, 2058, 2059');
    const skillsInput = page.getByPlaceholder('ex: 9153, 9154, 9155');
    const contextInput = page.getByPlaceholder('WvW Zerg, Roaming, PvE...');

    await specInput.fill(String(REAPER_SPEC_ID));
    await traitsInput.fill(REAPER_TRAITS.join(', '));
    await skillsInput.fill(REAPER_SKILLS.join(', '));
    await contextInput.fill('WvW Zerg Reaper power DPS marauder');

    const analyzeButton = page.getByRole('button', { name: /analyser la synergie/i }).first();
    await analyzeButton.click();

    const resultContainer = page.getByText(/résultat/i).first();
    await expect(resultContainer).toBeVisible({ timeout: 30_000 });

    // Pour un build DPS, on s'attend à voir le DPS de rotation
    const dpsLabel = page.getByText(/DPS rotation \(10s\)/i).first();
    await expect(dpsLabel).toBeVisible({ timeout: 30_000 });

    // Comparaison méta
    const metaHeading = page.getByText(/comparaison avec la méta/i).first();
    await expect(metaHeading).toBeVisible({ timeout: 30_000 });

    const similarityBadge = page.getByText(/% similaire/i).first();
    await expect(similarityBadge).toBeVisible();
  });
});
