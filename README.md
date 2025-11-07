# GW2Optimizer

Guild Wars 2 build & team optimization platform pilotée par IA — alimentée par des connecteurs de données, un pipeline de normalisation et une synchronisation hebdomadaire automatique.

## Vision : IA auto-mise-à-jour
1. **Connecteurs de données** : API GW2 officielle, Wiki, sources communautaires.
2. **Pipeline de normalisation** : schémas unifiés, indexation vectorielle optionnelle (RAG) et expiration contrôlée.
3. **Orchestration** : planification/monitoring des jobs de rafraîchissement et métriques d’alerte.
4. **Boucle LLM** : rafraîchissement contextuel continu avec stratégies de fallback.

## Quick start
```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
uvicorn app.main:app --app-dir backend/app --host 0.0.0.0 --port 8000

# Frontend
cp frontend/.env.development.example frontend/.env.development   # puis ajuster VITE_API_BASE_URL si besoin
npm --prefix frontend install
npm --prefix frontend run dev

# Tests
pytest -q backend/tests
npm --prefix frontend test
npm --prefix frontend run test:e2e   # optionnel (Playwright)
```

## Configuration backend (local par défaut)
- `BASE_URL_BACKEND` : URL externe publiée par l'API (défaut `http://localhost:8000`).
- `ALLOWED_ORIGINS` : origines autorisées via CORS (JSON ou liste séparée par des virgules, défaut `http://localhost:5173`).
- `COOKIE_DOMAIN` : domaine appliqué aux cookies d'auth (laisser vide en local).
- `COOKIE_SECURE` : `false` en dev, `true` derrière HTTPS en prod.
- `COOKIE_SAMESITE` : `lax` en dev (`none` si SPA + cookies cross-site via HTTPS).
- `COOKIE_MAX_AGE` : durée personnalisée (en secondes) pour les cookies auth.
- `DEFAULT_RATE_LIMIT` : limite SlowAPI globale (défaut `60/minute`).
- `ML_TRAINING_ENABLED` : active le déclenchement incrémental du modèle de synergie lorsque des feedbacks sont reçus (false par défaut).
- `LEARNING_DATA_DIR` : répertoire où les feedbacks sont stockés en JSON lors du fallback (`backend/data/learning/feedback`).
- `SERVER_HEADER` : laissez vide pour s'en remettre au proxy (recommandé) ou définissez une valeur custom; éviter d'exposer la stack (ex.: via Traefik/Nginx `proxy_hide_header Server`).

Voir `docs/RUNBOOKS/backend.md` pour les détails d'exploitation et `docs/RUNBOOKS/ci.md` pour la CI.

## Boucle de feedback IA & entraînement incrémental

- **Endpoint** : `POST /api/v1/ai/feedback` (payload minimal : `target_id`, `rating`, optionnel `comment`/`meta`).
- **Persistance** : la couche `FeedbackHandler` traite le feedback. En cas d'échec, un fallback JSON est écrit dans `LEARNING_DATA_DIR`.
- **Déclencheur ML** : si `ML_TRAINING_ENABLED=true`, l'API planifie une tâche de fond qui appelle `trigger_incremental_training` (asynchrone, non bloquant pour l'appelant).
- **Metrics Prometheus** (soft) :
  - `ai_feedback_total{result="ok|fallback|error"}`
  - `ai_training_triggers_total{result="scheduled|disabled|error"}`
- **Authentification** : l'endpoint accepte les utilisateurs authentifiés ou anonymes; l'ID utilisateur est injecté si disponible.

Pour tester localement :

```bash
curl -X POST http://localhost:8000/api/v1/ai/feedback \
  -H "Content-Type: application/json" \
  -d '{"target_id":"comp-42","rating":9,"comment":"Très bon"}'
```

Activer l'entraînement incrémental en exportant `ML_TRAINING_ENABLED=true` (ou via `.env`).

## Frontend Phase 2 (auth + dashboards)
- `VITE_API_BASE_URL` : base API utilisée par Axios (`frontend/.env.development`).
- Store global (Zustand) pour l'état d'auth (`frontend/src/store/auth.ts`).
- Intercepteurs Axios (401 → hooks store à venir) et tests unitaires (`npm -C frontend test`).

## Maintenance

### Déclencher le workflow de nettoyage (`cleanup_purge.yml`)

```bash
# Dry-run (rapport uniquement, aucune suppression)
gh workflow run ".github/workflows/cleanup_purge.yml" \
  -f dry_run=true \
  -f purge_all=false \
  -f close_prs=false \
  -f close_issues=false

# Purge réelle (attention : supprime branches, ferme PRs et issues)
gh workflow run ".github/workflows/cleanup_purge.yml" \
  -f dry_run=false \
  -f purge_all=true \
  -f close_prs=true \
  -f close_issues=true
```

## Liens utiles
- [ROADMAP](ROADMAP.md)
- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [SECURITY](SECURITY.md)
- [audit / rapports sécurité](audit-reports/audit.md)
- [docs/RUNBOOKS/backend.md](docs/RUNBOOKS/backend.md)
- [docs/RUNBOOKS/ci.md](docs/RUNBOOKS/ci.md)

## Stack actuelle
- **Backend** : FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Redis.
- **Frontend** : React + TypeScript (Vite, Vitest, Playwright).
- **Orchestration** : GitHub Actions (CI lint/test/codeql, docs guard, build docker local).
- **IA** : Intégrations prêtes pour modèles Mistral via pipelines internes.

## Contribution
Ce dépôt est maintenu en mode automatisé. Toute contribution passe par PR avec CI 100% verte et revue dédiée. Voir aussi [SECURITY.md](SECURITY.md) pour la gestion des risques connus.
