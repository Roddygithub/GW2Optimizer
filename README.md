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
npm --prefix frontend install
npm --prefix frontend run dev

# Tests
pytest -q backend/tests
npm --prefix frontend test
npm --prefix frontend run test:e2e   # optionnel (Playwright)
```

## Liens utiles
- [ROADMAP](ROADMAP.md)
- [ARCHITECTURE](docs/ARCHITECTURE.md)
- [SECURITY](SECURITY.md)
- [audit / rapports sécurité](audit-reports/audit.md)

## Stack actuelle
- **Backend** : FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Redis.
- **Frontend** : React + TypeScript (Vite, Vitest, Playwright).
- **Orchestration** : GitHub Actions (CI lint/test/codeql, docs guard, build docker local).
- **IA** : Intégrations prêtes pour modèles Mistral via pipelines internes.

## Contribution
Ce dépôt est maintenu en mode automatisé. Toute contribution passe par PR avec CI 100% verte et revue dédiée. Voir aussi [SECURITY.md](SECURITY.md) pour la gestion des risques connus.
