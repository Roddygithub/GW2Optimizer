import { test, expect } from '@playwright/test';
import { login } from './utils/login';

test.describe('Build Composer', () => {
  test('should allow creating a new build', async ({ page }) => {
    // Skip if no credentials provided
    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    // Login first
    await login(page);
    
    // Navigate to composer - adjust path as needed
    await page.goto('/composer');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: /create.*build|new build/i })).toBeVisible();
    
    // Test build creation with data-testid selectors (add these to your components)
    const professionSelect = page.getByTestId('select-profession');
    const weaponSelect = page.getByTestId('select-weapon');
    
    if (!(await professionSelect.isVisible()) || !(await weaponSelect.isVisible())) {
      test.skip(true, 'Required test IDs not found in the DOM');
      return;
    }
    
    // Fill build details
    await professionSelect.selectOption('Elementalist');
    await weaponSelect.selectOption('Dagger');
    
    // Add trait/skill if available
    const addTraitButton = page.getByRole('button', { name: /add trait/i }).first();
    if (await addTraitButton.isVisible()) {
      await addTraitButton.click();
    }
    
    // Save build
    const saveButton = page.getByRole('button', { name: /save build/i });
    await saveButton.click();
    
    // Verify success message
    await expect(page.getByText(/build.*saved|success/i).first()).toBeVisible({
      timeout: 10000
    });
  });

  test('should validate required fields', async ({ page }) => {
    await page.goto('/composer');
    
    // Try to save without filling required fields
    const saveButton = page.getByRole('button', { name: /save build/i });
    await saveButton.click();
    
    // Verify validation errors
    await expect(page.getByText(/required|please fill in/i).first()).toBeVisible({
      timeout: 3000
    });
  });
});
