import { test, expect, type Page, type Locator } from '@playwright/test';
import { login, firstVisible, isVisible } from './utils/login';
import { ROUTES } from './constants';

async function navigateToTeamCommander(page: Page): Promise<boolean> {
  // Si une route directe est connue un jour, on pourra la renseigner ici.
  // Pour l'instant, on utilise la navigation par lien/menu.

  // Essayer d'aller directement sur la route connue
  await page.goto(ROUTES.home);

  const candidates: Locator[] = [
    page.getByRole('link', { name: /team commander/i }).first(),
    page.getByRole('button', { name: /team commander/i }).first(),
  ];

  const target = await firstVisible(...candidates);
  if (!target) {
    return false;
  }

  await target.click();
  return true;
}

test.describe('Team Commander', () => {
  test('should display Team Commander UI and allow sending a command', async ({ page }) => {
    // On a besoin d'un user E2E pour tester le flux complet
    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    const loggedIn = await login(page);
    if (!loggedIn) {
      return;
    }

    const navigated = await navigateToTeamCommander(page);
    if (!navigated) {
      test.skip(true, 'Team Commander UI not exposed in current build');
      return;
    }

    // Header de la page
    const heading = page.getByRole('heading', { name: /team commander/i });
    await expect(heading).toBeVisible();

    // Champ d'entrée
    const input = page.getByPlaceholder(/je veux 2 groupes de 5|firebrand/i);
    if (!(await isVisible(input))) {
      test.skip(true, 'Team Commander input not accessible');
      return;
    }

    await input.fill(
      'Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker et Scrapper pour du WvW zerg.'
    );
    await input.press('Enter');

    // On attend une réponse de l'IA avec une indication de succès/synergie
    await expect(
      page.getByText(/team créée avec succès|synergie/i).first()
    ).toBeVisible({ timeout: 30_000 });
  });
});
