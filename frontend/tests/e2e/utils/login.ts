import process from 'node:process';
import { test, expect, type Page, type Locator } from '@playwright/test';
import { ROUTES, LABELS } from '../constants';

export async function isVisible(locator?: Locator | null) {
  if (!locator) return false;
  try {
    return await locator.isVisible();
  } catch {
    return false;
  }
}

export async function firstVisible(...locators: Locator[]) {
  for (const locator of locators) {
    if (await isVisible(locator)) {
      return locator;
    }
  }
  return null;
}

export async function login(page: Page): Promise<boolean> {
  const email = process.env.E2E_USER;
  const password = process.env.E2E_PASS;

  if (!email || !password) {
    test.skip(true, 'E2E_USER/PASS environment variables not set');
    return false;
  }

  // Pour les E2E, on ne teste pas le flux UI de login mais le Build Lab.
  // On simule donc une session authentifiée en injectant des tokens dans localStorage
  // avant de charger l'application protégée.

	page.on('pageerror', (error) => {
		// eslint-disable-next-line no-console
		console.log('[E2E][pageerror]', error.message);
	});

	page.on('console', (msg) => {
		// eslint-disable-next-line no-console
		console.log(`[E2E][console][${msg.type()}]`, msg.text());
	});

  await page.addInitScript(() => {
    window.localStorage.setItem('access_token', 'e2e-token');
    window.localStorage.setItem('refresh_token', 'e2e-token');
  });

  // Naviguer directement vers la home protégée (Dashboard)
  await page.goto(ROUTES.home ?? '/');

  // Vérifier simplement que le contenu protégé est accessible
  await page.waitForLoadState('networkidle');
  return true;
}

export async function logout(page: Page) {
  const userMenu = page.locator('[data-testid="user-menu"]');

  if (await isVisible(userMenu)) {
    await userMenu.click();
    const menuItem = await firstVisible(
      page.getByRole('menuitem', { name: /sign out|log out/i }).first(),
      page.getByRole('menuitem', { name: /déconnexion/i }).first()
    );
    if (menuItem) {
      await menuItem.click();
    }
  } else {
    const logoutButton = await firstVisible(
      page.getByRole('button', { name: /déconnexion/i }).first(),
      page.getByRole('button', { name: /sign out|log out/i }).first()
    );
    if (logoutButton) {
      await logoutButton.click();
    }
  }

  await expect(
    page.getByRole('heading', { name: /connexion|login|sign in/i }).first()
  ).toBeVisible({ timeout: 10_000 });
}

// Export des fonctions pour les tests
