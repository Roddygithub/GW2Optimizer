# Roadmap

## Milestones

### 1. Connecteurs de données
- Couvrir l'API officielle Guild Wars 2 (professions, spécialisations, builds de référence).
- Synchroniser Wiki et sources communautaires (MetaBattle, SnowCrows, Hardstuck).
- Historiser les diffs pour permettre la comparaison entre patchs de jeu.

### 2. Normalisation & stockage
- Définir des schémas unifiés pour builds, équipes et métadonnées.
- Indexation vectorielle optionnelle (RAG) pour requêtes contextuelles.
- Politique d’expiration/rafraîchissement pour garder un corpus “fraîcheur < 7 jours”.

### 3. Schedule & monitoring
- Planifier les jobs hebdomadaires (GitHub Actions / cron interne) avec ré-exécutions automatiques.
- Exposer métriques Prometheus (fraîcheur des données, taux de succès jobs, latence connecteurs).
- Alerter via Slack/Discord en cas d’échec ou dérive (>24h de retard).

### 4. Intégration LLM
- Pipeline d’enrichissement contextuel (prompt + retrieval) pour chaque connecteur.
- Stratégies de fallback : cache local, dernier snapshot valide, mode dégradé sans IA.
- Validation automatique des réponses (contrôles métier, détection hallucinations).

### 5. E2E réels (required)
- Couvrir un scénario complet : login, sélection build, composition d’équipe, export.
- Générer des artefacts Playwright (HTML/JSON) et marquer le job comme “required”.
- Documenter runbooks (échec E2E, données manquantes, ré-exécution).
