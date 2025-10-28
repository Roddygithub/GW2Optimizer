import { test, expect } from '@playwright/test';
import { login } from './utils/login';

test.describe('Export', () => {
  test('should export build as JSON', async ({ page }) => {
    // Skip if no credentials provided
    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    // Login first
    await login(page);
    
    // Navigate to a build or create one
    await page.goto('/my-builds');
    
    // Wait for builds to load
    await expect(page.getByRole('heading', { name: /my builds/i })).toBeVisible();
    
    // Click on first build - adjust selector as needed
    const firstBuild = page.getByRole('link', { name: /view|edit/i }).first();
    if (!(await firstBuild.isVisible())) {
      test.skip(true, 'No builds found to export');
      return;
    }
    
    await firstBuild.click();
    
    // Click export button
    const exportButton = page.getByRole('button', { name: /export/i });
    await exportButton.click();
    
    // In the export dialog, click JSON export
    const jsonButton = page.getByRole('button', { name: /export.*json/i });
    await jsonButton.click();
    
    // Verify success message
    await expect(page.getByText(/export.*success|copied to clipboard/i)).toBeVisible({
      timeout: 10000
    });
  });

  test('should show export options for a build', async ({ page }) => {
    await page.goto('/export');
    
    // Verify export options are visible
    await expect(page.getByRole('heading', { name: /export.*build/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /export.*json/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /export.*image/i })).toBeVisible();
  });
});
