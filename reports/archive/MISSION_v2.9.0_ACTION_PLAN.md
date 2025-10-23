# 🎯 MISSION v2.9.0 - ACTION PLAN

**Date**: 2025-10-22 23:40 UTC+02:00  
**Objective**: 257/257 tests GREEN + 60% frontend coverage + Monitoring + E2E  
**Duration**: 4 semaines

---

## 📊 ÉTAT ACTUEL (v2.8.0)

### Backend
- ✅ Critical: 79/79 (100%)
- ⚠️ Legacy: 25 tests marked
- Total: 218/257 (85%)

### Frontend
- ✅ Tests: 22/22 (100%)
- ⚠️ Coverage: 25.72%
- Target: 60%+

### Infrastructure
- ✅ CI optimized
- ❌ Monitoring: Not setup
- ❌ E2E: Not setup

---

## 🗓️ PHASE 1: LEGACY CLEANUP (Semaine 1)

### Objectif
Fix 25 tests legacy → 257/257 tests GREEN

### Tests à Fixer

**test_exporter.py (9 tests)**
```python
# Problem: Build objects missing required fields
# Solution: Add factory function

def create_test_build(**kwargs):
    defaults = {
        'id': str(uuid4()),
        'user_id': str(uuid4()),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }
    return Build(**{**defaults, **kwargs})
```

**test_build_service.py (10 tests)**
```python
# Problem: UUID format issues
# Solution: Use proper UUID strings

user_id = str(uuid4())  # Not uuid4() directly
```

**Autres (6 tests)**
- test_scraper.py: 1 test
- test_synergy_analyzer.py: 1 test (test_empty_team)
- test_health.py: 1 test
- test_teams.py: 2 tests
- test_websocket_mcm.py: 1 test

### Commandes Manuel

```bash
cd backend

# Identifier tests legacy
grep -r "@pytest.mark.legacy" tests/

# Tester un fichier spécifique
pytest tests/test_exporter.py -v

# Tester tous les legacy
pytest -m legacy -v

# Vérifier après fix
pytest -m 'not legacy' -v  # Should still be 79/79
pytest -m legacy -v        # Should be 25/25
pytest -v                  # Should be 257/257
```

### Livrable
- ✅ 257/257 tests GREEN
- ✅ Legacy tests intégrés
- ✅ CI passe avec tous les tests

---

## 🎨 PHASE 2: FRONTEND COVERAGE 60%+ (Semaine 2)

### Objectif
Passer de 25.72% à 60%+ coverage

### Composants à Tester

**Dashboard.tsx (priorité haute)**
```typescript
// tests/Dashboard.test.tsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';

describe('Dashboard', () => {
  test('renders welcome message', () => {
    render(<Dashboard />);
    expect(screen.getByText(/Welcome/i)).toBeInTheDocument();
  });
  
  test('displays user stats', () => {
    render(<Dashboard />);
    expect(screen.getByText(/Builds/i)).toBeInTheDocument();
  });
});
```

**AuthContext.tsx**
```typescript
// tests/AuthContext.test.tsx
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../context/AuthContext';

describe('AuthContext', () => {
  test('provides auth state', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider
    });
    expect(result.current.isAuthenticated).toBe(false);
  });
});
```

**api.ts services**
```typescript
// tests/api.test.ts
import { vi } from 'vitest';
import { login, getBuilds } from '../services/api';

describe('API Services', () => {
  test('login calls correct endpoint', async () => {
    global.fetch = vi.fn(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ token: 'abc' })
      })
    );
    
    await login('user', 'pass');
    expect(fetch).toHaveBeenCalledWith('/api/auth/login', expect.any(Object));
  });
});
```

### Commandes Manuel

```bash
cd frontend

# Lancer tests avec coverage
npm run test:coverage -- --run

# Voir rapport HTML
open coverage/index.html

# Tester fichier spécifique
npm test -- Dashboard.test.tsx --run
```

### Livrable
- ✅ 60%+ coverage frontend
- ✅ Tests Dashboard, AuthContext, api.ts
- ✅ CI vérifie coverage threshold

---

## 📊 PHASE 3: MONITORING (Semaine 3)

### Objectif
Prometheus + Grafana + Sentry opérationnels

### 3.1 Prometheus + Grafana

**docker-compose.monitoring.yml**
```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus_data:
  grafana_data:
```

**monitoring/prometheus.yml**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'gw2optimizer-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

**Backend Integration**
```python
# backend/requirements.txt
prometheus-fastapi-instrumentator==6.1.0

# backend/app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Add metrics endpoint
if not settings.TESTING:
    Instrumentator().instrument(app).expose(app)
```

### 3.2 Sentry

**Backend**
```python
# backend/requirements.txt
sentry-sdk[fastapi]==1.40.0

# backend/app/main.py
import sentry_sdk

if not settings.TESTING and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=settings.ENVIRONMENT
    )
```

**Frontend**
```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [new Sentry.BrowserTracing()],
    tracesSampleRate: 1.0,
  });
}
```

### Commandes Manuel

```bash
# Lancer monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Vérifier Prometheus
curl http://localhost:9090/-/healthy

# Vérifier métriques backend
curl http://localhost:8000/metrics

# Accéder Grafana
open http://localhost:3000
# Login: admin / admin
```

### Livrable
- ✅ Prometheus scraping backend metrics
- ✅ Grafana dashboards opérationnels
- ✅ Sentry error tracking backend + frontend
- ✅ Logs centralisés

---

## 🎭 PHASE 4: E2E PLAYWRIGHT (Semaine 4)

### Objectif
Tests E2E automatiques avec Playwright

### 4.1 Setup Playwright

```bash
cd frontend

# Installation
npm install -D @playwright/test
npx playwright install chromium
```

**playwright.config.ts**
```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 4.2 Tests E2E Critiques

**e2e/auth.spec.ts**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can login', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpass');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });
  
  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="username"]', 'wrong');
    await page.fill('[name="password"]', 'wrong');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});
```

**e2e/builds.spec.ts**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Builds Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpass');
    await page.click('button[type="submit"]');
  });
  
  test('can create new build', async ({ page }) => {
    await page.goto('/builds/new');
    await page.fill('[name="name"]', 'Test Build');
    await page.selectOption('[name="profession"]', 'Guardian');
    await page.selectOption('[name="gameMode"]', 'zerg');
    await page.click('button:has-text("Create")');
    await expect(page.locator('text=Build created')).toBeVisible();
  });
});
```

**e2e/teams.spec.ts**
```typescript
import { test, expect } from '@playwright/test';

test.describe('Team Composition', () => {
  test('can create team', async ({ page }) => {
    await page.goto('/teams/new');
    await page.fill('[name="name"]', 'Test Team');
    await page.fill('[name="teamSize"]', '10');
    await page.click('button:has-text("Create Team")');
    await expect(page.locator('text=Team created')).toBeVisible();
  });
});
```

### 4.3 CI Integration

**.github/workflows/e2e.yml**
```yaml
name: E2E Tests

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  e2e:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Start backend
        run: |
          cd backend
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test
          TESTING: "false"
      
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Install Playwright
        run: |
          cd frontend
          npx playwright install --with-deps chromium
      
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30
```

### Commandes Manuel

```bash
cd frontend

# Lancer E2E tests
npx playwright test

# Mode UI interactif
npx playwright test --ui

# Debug mode
npx playwright test --debug

# Voir rapport
npx playwright show-report
```

### Livrable
- ✅ Playwright configuré
- ✅ Tests E2E auth, builds, teams
- ✅ CI workflow E2E
- ✅ Artifacts HTML générés

---

## 🔄 PHASE 5: CI/CD INTEGRATION

### Workflow Complet

**.github/workflows/ci-complete.yml**
```yaml
name: CI/CD Complete

on:
  push:
    branches: [main, dev]
  pull_request:

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run critical tests
        run: |
          cd backend
          pytest -m 'not legacy' --cov=app --cov-report=xml
      - name: Run all tests
        continue-on-error: true
        run: |
          cd backend
          pytest --cov=app --cov-report=xml:coverage-all.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests with coverage
        run: |
          cd frontend
          npm run test:coverage -- --run
      - name: Check coverage threshold
        run: |
          cd frontend
          npm run test:coverage -- --run --coverage.thresholds.lines=60
  
  e2e-tests:
    needs: [backend-tests, frontend-tests]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-report
          path: frontend/playwright-report/
```

---

## 📋 CHECKLIST v2.9.0

### Backend
- [ ] Fix 25 tests legacy
- [ ] 257/257 tests GREEN
- [ ] Prometheus metrics endpoint
- [ ] Sentry integration

### Frontend
- [ ] Tests Dashboard.tsx
- [ ] Tests AuthContext.tsx
- [ ] Tests api.ts
- [ ] 60%+ coverage
- [ ] Sentry integration

### Monitoring
- [ ] Prometheus running
- [ ] Grafana dashboards
- [ ] Sentry backend configured
- [ ] Sentry frontend configured

### E2E
- [ ] Playwright installed
- [ ] Tests auth flow
- [ ] Tests builds CRUD
- [ ] Tests teams CRUD
- [ ] CI workflow E2E

### CI/CD
- [ ] All workflows passing
- [ ] Coverage thresholds enforced
- [ ] Artifacts uploaded
- [ ] Documentation updated

---

## 🎯 SUCCESS CRITERIA

### Must Have
- ✅ 257/257 tests GREEN (100%)
- ✅ Frontend coverage ≥ 60%
- ✅ Monitoring operational
- ✅ E2E tests passing

### Should Have
- ✅ Grafana dashboards
- ✅ Sentry error tracking
- ✅ CI artifacts 30 days
- ✅ Complete documentation

### Nice to Have
- Performance benchmarks
- Load testing (k6)
- Auto-scaling config

---

## 📊 TIMELINE

```
Semaine 1: Legacy Cleanup
├─ Jour 1-2: Fix test_exporter.py (9 tests)
├─ Jour 3-4: Fix test_build_service.py (10 tests)
└─ Jour 5: Fix autres (6 tests) + validation

Semaine 2: Frontend Coverage
├─ Jour 1-2: Tests Dashboard + AuthContext
├─ Jour 3-4: Tests api.ts + utils
└─ Jour 5: Validation coverage 60%+

Semaine 3: Monitoring
├─ Jour 1-2: Prometheus + Grafana setup
├─ Jour 3-4: Sentry backend + frontend
└─ Jour 5: Dashboards + validation

Semaine 4: E2E Tests
├─ Jour 1-2: Playwright setup + tests auth
├─ Jour 3-4: Tests builds + teams
└─ Jour 5: CI integration + validation
```

---

## 🚀 NEXT STEPS

1. **Commencer Phase 1** (Legacy Cleanup)
2. **Tester localement** avant commit
3. **Commit par phase** (atomic changes)
4. **Valider CI** après chaque phase
5. **Documenter** au fur et à mesure

**Ready to start v2.9.0!**
