# Tests E2E · AI Build Lab & Mes Builds

Ce dossier contient les tests End-to-End Playwright pour l'interface AI Build Lab, le Team Commander et la page Mes Builds.

## Prérequis

- Docker & Docker Compose installés
- Image Playwright : `mcr.microsoft.com/playwright:v1.48.0-jammy`
- Variables d'environnement E2E côté tests :
  - `E2E_USER="test@example.com"`
  - `E2E_PASS="TestPass123!"`

L'utilisateur E2E peut être créé via le script backend (voir ci-dessous).

## 1. Démarrer la stack backend + frontend

Depuis la racine du repo :

```bash
docker compose -f docker-compose.prod.yml up -d backend frontend postgres redis
```

- Backend : http://localhost:8000
- Frontend : http://localhost:80

## 2. Créer l'utilisateur E2E

Dans le conteneur backend :

```bash
docker exec -it gw2optimizer-backend bash -lc "python backend/scripts/legacy/create_test_user.py"
```

Par défaut :

- Email : `test@example.com`
- Mot de passe : `TestPass123!`

## 3. Lancer les tests E2E avec Playwright (Docker)

Depuis le dossier `frontend/` **sur l'hôte** :

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  -e E2E_USER="test@example.com" \
  -e E2E_PASS="TestPass123!" \
  -e E2E_BASE_URL="http://host.docker.internal:80" \
  mcr.microsoft.com/playwright:v1.48.0-jammy \
  bash -lc "npm ci && npx playwright install --with-deps && npx playwright test"
```

Cela exécute **tous** les tests E2E dans `tests/e2e`.

### 3.1 Lancer uniquement les tests AI Build Lab (Firebrand + Reaper + Save)

Toujours depuis `frontend/` :

```bash
docker run --rm -it \
  -v "$PWD":/work \
  -w /work \
  -e E2E_USER="test@example.com" \
  -e E2E_PASS="TestPass123!" \
  -e E2E_BASE_URL="http://host.docker.internal:80" \
  mcr.microsoft.com/playwright:v1.48.0-jammy \
  bash -lc "npm ci && npx playwright install --with-deps && npx playwright test \
    tests/e2e/ai-build-lab-firebrand.spec.ts \
    tests/e2e/ai-build-lab-reaper.spec.ts \
    tests/e2e/ai-build-lab-firebrand-save.spec.ts"
```

## 4. Résumé des scénarios AI Build Lab

- `ai-build-lab-firebrand.spec.ts`  
  Build Firebrand support WvW : vérifie HPS de rotation + comparaison avec la méta.

- `ai-build-lab-reaper.spec.ts`  
  Build Reaper power DPS : vérifie DPS de rotation + comparaison méta, sans HPS.

- `ai-build-lab-firebrand-save.spec.ts`  
  Build Firebrand support → sauvegarde dans "Mes Builds" → vérifie la présence du build sauvegardé dans le tableau.
