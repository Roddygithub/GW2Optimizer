import { test, expect } from '@playwright/test';
import { login, logout } from './utils/login';

test.describe('Authentication', () => {
  test('should allow user to log in and log out', async ({ page }) => {
    // Skip if no credentials provided
    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    await page.goto('/');
    
    // Test login
    await login(page);
    
    // Verify login success - adjust selector based on your app
    await expect(page.getByText(/welcome|dashboard|home/i).first()).toBeVisible();
    
    // Test logout
    await logout(page);
    
    // Verify logout success
    await expect(page.getByRole('link', { name: /login|sign in/i }).first()).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill with invalid credentials
    await page.getByLabel(/email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in|login/i }).click();
    
    // Verify error message
    await expect(page.getByText(/invalid.*credentials|wrong.*password/i).first()).toBeVisible({
      timeout: 5000
    });
  });
});
