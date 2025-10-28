import { test, expect, type Page } from '@playwright/test';

export async function login(page: Page) {
  const email = process.env.E2E_USER;
  const password = process.env.E2E_PASS;
  
  if (!email || !password) {
    test.skip(true, 'E2E_USER/PASS environment variables not set');
    return;
  }

  await page.goto('/');
  
  // Try to find and click login link/button
  const loginButton = page.getByRole('link', { name: /login|sign in/i }).first();
  if (await loginButton.isVisible()) {
    await loginButton.click();
  }
  
  // Fill login form
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in|login/i }).click();
  
  // Wait for login to complete
  await expect(page.getByText(/welcome|dashboard|home/i).first()).toBeVisible({ timeout: 10000 });
}

export async function logout(page: Page) {
  const userMenu = page.locator('[data-testid="user-menu"]');
  if (await userMenu.isVisible()) {
    await userMenu.click();
    await page.getByRole('menuitem', { name: /sign out|log out/i }).click();
    await expect(page.getByText(/signed out|logged out/i).first()).toBeVisible({ timeout: 5000 });
  }
}

// Export des fonctions pour les tests
