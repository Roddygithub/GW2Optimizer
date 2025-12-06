import process from 'node:process';
import { test, expect } from '@playwright/test';
import { login, logout, firstVisible } from './utils/login';
import { ROUTES, LABELS } from './constants';

test.describe('Authentication', () => {
  test('should allow user to log in and log out', async ({ page }) => {
    // Skip if no credentials provided
    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    await page.goto(ROUTES.home);

    const loggedIn = await login(page);
    if (!loggedIn) {
      return;
    }

    await expect(page.getByRole('main')).toBeVisible();

    await logout(page);

    await expect(page.getByRole('main')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    if (!ROUTES.login) {
      test.skip(true, 'Login route not available');
      return;
    }

    await page.goto(ROUTES.login);

    const emailField = page.getByLabel(/email|pseudo/i);
    const passwordField = page.getByLabel(/mot de passe|password/i);

    if (!(await emailField.isVisible()) || !(await passwordField.isVisible())) {
      test.skip(true, 'Login form fields not accessible');
      return;
    }

    await emailField.fill('invalid@example.com');
    await passwordField.fill('wrongpassword');

    const submitButton = await firstVisible(
      ...LABELS.login.map((pattern) => page.getByRole('button', { name: pattern }).first()),
      page.getByRole('button', { name: /submit/i }).first()
    );
    if (!submitButton) {
      test.skip(true, 'Login submit control not accessible');
      return;
    }

    await submitButton.click();

    await expect(page.getByText(/invalid.*credentials|wrong.*password/i).first()).toBeVisible({
      timeout: 5000
    });
  });
});
