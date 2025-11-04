# Audit – état au 2025-11-03

## Résumé
- **Back-end** : lint (Ruff/Black) et tests Pytest passent localement (dernière exécution 2025-11-02). Couverture >90% maintenue.
- **Front-end** : Vitest OK (51 tests). Couverture encore ~49% — suivie dans la roadmap « Connecteurs & pipeline ».
- **CI/CD** : workflows revus (lint → tests → CodeQL → build docker). Actionlint via job dédié « lint-workflows ».
- **Sécurité** : aucun package critique détecté par pip-audit/npm audit (2025-11-01). Risque connu `ecdsa` documenté dans [SECURITY.md](../SECURITY.md).

## Points de vigilance
1. **Couverture frontend** : viser ≥60% avant d’augmenter les seuils CI.
2. **E2E** : tests Playwright en mode `continue-on-error`; action item pour les rendre « required » (voir ROADMAP).
3. **Temps de pipeline** : monitoring en cours (branch `main`). Garder un œil sur les jobs >12 min.

## Actions ouvertes
- Issues planifiées (voir section “Ouvertures” de la RFC 0001 et ROADMAP) :
  - Connecteurs GW2 officiels & communautaires.
  - Pipeline de normalisation + indexation vectorielle.
  - Orchestration & alerting.
  - Rafraîchissement LLM auto.
  - E2E scénarios complets.

## Annexes
- Derniers rapports disponibles dans ce dossier (`*.json`, `playwright/`, `pip-audit.json`).
- Historique détaillé déplacé vers `docs/legacy/`.
