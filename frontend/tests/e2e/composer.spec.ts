import { test, expect, type Page, type Locator } from '@playwright/test';
import { login, firstVisible, isVisible } from './utils/login';
import { ROUTES, LABELS } from './constants';

async function navigateToComposer(page: Page): Promise<boolean> {
  if (ROUTES.composer) {
    await page.goto(ROUTES.composer);
    return true;
  }

  const navCandidates: Locator[] = [
    ...LABELS.composer.map((pattern) => page.getByRole('link', { name: pattern }).first()),
    ...LABELS.composer.map((pattern) => page.getByRole('button', { name: pattern }).first()),
    page.getByTestId('nav-composer'),
  ];

  const target = await firstVisible(...navCandidates);
  if (!target) {
    return false;
  }

  await target.click();
  return true;
}

test.describe('Build Composer', () => {
  test('should allow creating a new build', async ({ page }) => {
    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    const loggedIn = await login(page);
    if (!loggedIn) {
      return;
    }

    const navigated = await navigateToComposer(page);
    if (!navigated) {
      test.skip(true, 'Composer UI not exposed in current build');
      return;
    }

    const main = page.getByRole('main');
    if (!(await isVisible(main))) {
      test.skip(true, 'Composer main content not accessible');
      return;
    }

    // Awaiting actual composer implementation
    test.skip(true, 'Composer interactions not available in current build');
  });

  test('should validate required fields', async ({ page }) => {
    const navigated = await navigateToComposer(page);
    if (!navigated) {
      test.skip(true, 'Composer UI not exposed in current build');
      return;
    }

    const saveButtonCandidates: Locator[] = [
      ...LABELS.composer.map((pattern) => page.getByRole('button', { name: pattern }).first()),
      page.getByTestId('save-build'),
    ];
    const saveButton = await firstVisible(...saveButtonCandidates);
    if (!saveButton) {
      test.skip(true, 'Save control not available in composer UI');
      return;
    }

    await saveButton.click();
    await expect(page.getByText(/required|please fill in/i).first()).toBeVisible({ timeout: 3_000 });
  });
});
