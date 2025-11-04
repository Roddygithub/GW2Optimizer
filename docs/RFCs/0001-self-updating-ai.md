# RFC 0001 — IA auto-mise-à-jour

## Objectif
- Garantir que GW2Optimizer reste synchronisé avec l’écosystème Guild Wars 2 sans intervention manuelle.
- Couvrir la collecte, la normalisation et la diffusion continue des données de builds/équipes.
- Assurer la fiabilité métier (fraîcheur < 7 jours) et la traçabilité complète des mises à jour IA.

## Périmètre
- Connecteurs de données (API officielle GW2, Wiki, sources communautaires).
- Pipeline ETL (extraction, validation, normalisation, historisation).
- Stockage hybride (structurel + vectoriel) pour requêtes RAG.
- Orchestration (jobs planifiés, monitoring, alerting).
- Intégration LLM (rafraîchissement contextuel + stratégie de fallback).

### Hors périmètre
- Refactor complet du frontend (couvert par un projet séparé).
- Refonte des workflows de contribution communautaire.
- Modifications gameplay/équilibrage côté jeu.

## Architecture
1. **Connecteurs**
   - Workers Python asynchrones (httpx + pydantic) pour chaque source.
   - Cache de courtoisie (ETag/If-Modified-Since) + backoff adaptatif.
   - Validation contractuelle (schemas JSONSchema / pydantic). 

2. **Pipeline ETL**
   - File d’ingestion (Redis streams) → workers Celery/Arq.
   - Étapes : extraction → validation → enrichissement → versioning → publication.
   - Historisation : conservation des snapshots + diff calculé.
   - Normalisation : mapping commun (profession, rôle, boons, tags).

3. **Stockage**
   - PostgreSQL (tables normalisées builds/équipes/source).
   - Object storage (RAW JSON + artefacts HTML).
   - Index vectoriel (pgvector ou Qdrant) pour embeddings prompts.
   - Politique de rétention (TTL configurable, purge hebdo des snapshots obsolètes).

4. **Orchestration & Monitoring**
   - GitHub Actions planifiées (hebdomadaire + job manuel).
   - Export des métriques Prometheus (fraîcheur, succès, latence, taille corpus).
   - Alertes via Slack/Discord (webhook) sur échec ou dérive > 24h.
   - Tableau de bord Grafana « Data Freshness » + runbook incident.

5. **Boucle LLM**
   - Préparation du contexte : retrieval vectoriel + données structurées (Top builds, patch notes).
   - Prompts versionnés et testés (unitaires + golden datasets).
   - Stratégie de fallback : dernier snapshot valide, réponses templatisées.
   - Auditabilité : logs horodatés, hash des prompts/réponses, stockage dans S3-like.

## Plan de livraison
1. **Semaine 1-2**
   - Implémenter client GW2 API + scripts de sondage.
   - POC pipeline ingestion (Redis stream + worker async).
   - Création schémas normalisés (pydantic + migrations).

2. **Semaine 3-4**
   - Ajout connecteurs communautaires (MetaBattle, SnowCrows) + tests contractuels.
   - Mise en place historique diffs + endpoint d’observabilité (/data/status).
   - Déploiement métriques Prometheus + dashboard initial.

3. **Semaine 5-6**
   - Intégration pgvector/Qdrant + pipeline embeddings.
   - Premier jet prompts LLM (retrieval + backoff).
   - Mise en place alertes Slack/Discord + runbook incident.

4. **Semaine 7+**
   - Tests E2E complets (collecte → LLM → réponse API → UI).
   - Durcissement : load tests, chaos tests sur connecteurs.
   - Passage des jobs de synchronisation en « required » dans la CI.

## Indicateurs clés (SLO)
- Fraîcheur des builds prioritaires < 7 jours (p95).
- Taux de succès des jobs > 98% (rolling 30 jours).
- Temps de réponse pipeline ETL (ingestion → publication) < 10 min (p95).
- Score de confiance LLM (auto-évaluation + QA scripts) > 0.8.

## Ouvertures
- Ajouter des votes communautaires pondérés pour prioriser les ressources.
- Support multilingue pour prompts & données.
- API publique « self-updating » pour guildes tierces.
