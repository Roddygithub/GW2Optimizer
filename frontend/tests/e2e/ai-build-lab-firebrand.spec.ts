import process from 'node:process';
import { test, expect, type Page, type APIRequestContext } from '@playwright/test';
import { login, isVisible } from './utils/login';
import { ROUTES, API_BASE_URL } from './constants';

async function navigateToAiBuildLab(page: Page, accessToken: string): Promise<boolean> {
  // Set the access token in localStorage before navigating to the page
  await page.addInitScript((token) => {
    window.localStorage.setItem('access_token', token);
    window.localStorage.setItem('refresh_token', token);
  }, accessToken);

  const targetUrl = ROUTES.composer ?? ROUTES.home;
  await page.goto(targetUrl);
  await page.waitForLoadState('networkidle');

  const urlAfter = page.url();
  // eslint-disable-next-line no-console
  console.log('[E2E] navigateToAiBuildLab: after goto, URL:', urlAfter);
  const htmlAfter = await page.content();
  // eslint-disable-next-line no-console
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
    // Create URLSearchParams for form data
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

// IDs choisis depuis les dumps locaux GW2:
// - Spécialisation Firebrand: id = 62 (Guardian elite spec)
// - Trait "Liberator's Vow": id = 2101 (quickness sur heal)
// - Compétences Guardian heal/support: Shelter (id 9102), Mantra of Liberation (id 43357)

const FIREBRAND_SPEC_ID = 62;
const FIREBRAND_TRAITS = [2101];
const FIREBRAND_SKILLS = [9102, 43357];

test.describe('AI Build Lab - Firebrand Support HPS & Meta', () => {
  let request: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    // Create a new API context for making HTTP requests
    request = await playwright.request.newContext({
      baseURL: API_BASE_URL,
    });
  });

  test.afterAll(async () => {
    // Clean up the API context
    await request.dispose();
  });

  test('should compute HPS and show meta comparison for Firebrand support WvW', async ({ page }) => {
    test.setTimeout(120000); // Increase timeout to 2 minutes

    if (!process.env.E2E_USER || !process.env.E2E_PASS) {
      test.skip(true, 'E2E_USER/PASS environment variables not set');
      return;
    }

    // Login via API to get a valid token
    const accessToken = await loginAndGetToken(request);
    if (!accessToken) {
      test.fail(true, 'Failed to authenticate with the API');
      return;
    }

    // Navigate to AI Build Lab with the valid token
    const navigated = await navigateToAiBuildLab(page, accessToken);
    if (!navigated) {
      test.skip(true, 'AI Build Lab UI not exposed in current build');
      return;
    }

    // Attendre que la page soit chargée
    const main = page.getByRole('main');
    await expect(main).toBeVisible({ timeout: 30_000 });
    
    // Prendre une capture d'écran pour le débogage
    await page.screenshot({ path: 'debug-page-loaded.png' });
    
    // Remplir les champs avec un build Firebrand support WvW réaliste
    console.log('Remplissage des champs du formulaire...');
    
    // Attendre que les champs soient visibles
    const specInput = page.getByPlaceholder('ex: 62');
    const traitsInput = page.getByPlaceholder('ex: 2057, 2058, 2059');
    const skillsInput = page.getByPlaceholder('ex: 9153, 9154, 9155');
    const contextInput = page.getByPlaceholder('WvW Zerg, Roaming, PvE...');
    
    await expect(specInput).toBeVisible({ timeout: 10_000 });
    await expect(traitsInput).toBeVisible({ timeout: 10_000 });
    await expect(skillsInput).toBeVisible({ timeout: 10_000 });
    await expect(contextInput).toBeVisible({ timeout: 10_000 });
    
    // Remplir les champs
    await specInput.fill(String(FIREBRAND_SPEC_ID));
    await traitsInput.fill(FIREBRAND_TRAITS.join(', '));
    await skillsInput.fill(FIREBRAND_SKILLS.join(', '));
    await contextInput.fill('WvW Zerg Firebrand support heal quickness stability');
    
    console.log('Champs remplis, clic sur le bouton d\'analyse...');
    
    // Prendre une capture d'écran avant le clic
    await page.screenshot({ path: 'debug-before-click.png' });
    
    // Cliquer sur le bouton d'analyse
    const analyzeButton = page.getByRole('button', { name: /analyser la synergie|analyze/i }).first();
    await analyzeButton.click();
    
    console.log('Attente des résultats...');
    
    // Attendre que la section résultat soit affichée avec un timeout plus long
    const resultContainer = page.getByText(/(résultat|result)/i).first();
    await expect(resultContainer).toBeVisible({ timeout: 60_000 });
    
    // Prendre une capture d'écran après l'analyse
    await page.screenshot({ path: 'debug-after-analysis.png' });
    
    // Vérifier que l'HPS est affiché
    console.log('Recherche du label HPS...');
    const hpsLabel = page.getByText(/(HPS estimé \(rotation 10s\)|Estimated HPS \(10s rotation\))/i).first();
    await expect(hpsLabel).toBeVisible({ timeout: 30_000 });

    // Vérifier que la comparaison méta est affichée
    const metaHeading = page.getByText(/comparaison avec la méta/i).first();
    await expect(metaHeading).toBeVisible({ timeout: 30_000 });

    // Badge de similarité avec un pourcentage
    const similarityBadge = page.getByText(/% similaire/i).first();
    await expect(similarityBadge).toBeVisible();

    // Optionnel: vérifier qu'au moins une recommandation est affichée si présente
    const recommendationsTitle = page.getByText(/recommandations/i).first();
    if (await isVisible(recommendationsTitle)) {
      const recItem = page.getByText(/use|switch from|check|refer to/i).first();
      await expect(recItem).toBeVisible();
    }
  });
});
