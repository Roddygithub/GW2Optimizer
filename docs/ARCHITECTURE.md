# GW2Optimizer Architecture

## Overview

GW2Optimizer est un système d'optimisation d'équipes WvW pour Guild Wars 2 avec apprentissage automatique intégré.

## Structure du Projet

```
GW2Optimizer/
├── backend/              # Backend Python + FastAPI
│   ├── app/
│   │   ├── api/         # Routes API
│   │   ├── core/        # Configuration
│   │   ├── models/      # Modèles de données
│   │   └── services/    # Logique métier
│   └── tests/           # Tests backend
├── frontend/            # Frontend React + TypeScript
│   └── src/
│       ├── components/  # Composants React
│       └── services/    # API client
├── scripts/             # Scripts utilitaires
└── docs/                # Documentation
```

## Backend Architecture

### API Layer (`app/api/`)
- **health.py**: Health checks
- **chat.py**: Chatbot AI
- **builds.py**: Gestion des builds
- **teams.py**: Compositions d'équipes
- **learning.py**: Système d'apprentissage

### Services Layer (`app/services/`)

#### AI Services (`ai/`)
- **ollama_service.py**: Interface Ollama/Mistral
- **chat_service.py**: Service conversationnel

#### Learning System (`learning/`)
- **data_collector.py**: Collecte et compression
- **evaluator.py**: Évaluation automatique
- **selector.py**: Sélection des meilleurs builds
- **storage_manager.py**: Gestion de l'espace disque
- **trainer.py**: Fine-tuning du modèle
- **pipeline.py**: Orchestration automatique

#### Parser & Scraper
- **parser/gw2skill_parser.py**: Parse GW2Skill URLs
- **scraper/community_scraper.py**: Scraping communautaire

### Data Models (`app/models/`)
- **build.py**: Builds et configurations
- **team.py**: Compositions d'équipes
- **chat.py**: Messages de chat
- **learning.py**: Système d'apprentissage

## Frontend Architecture

### Components
- **ChatBox**: Interface de chat avec l'IA
- **BuildCard**: Carte de build
- **StatsPanel**: Statistiques d'apprentissage

### State Management
- React Query pour les requêtes API
- Local state avec useState

## Learning Pipeline

### 1. Collection
Chaque build/team généré est automatiquement collecté avec métadonnées et compressé.

### 2. Évaluation
L'IA évalue automatiquement la qualité selon :
- Synergies
- Couverture des rôles
- Conformité méta
- Validité technique

### 3. Sélection
Seuls les builds de haute qualité (score ≥7) sont sélectionnés pour l'entraînement.

### 4. Fine-tuning
Le modèle Mistral est ajusté périodiquement avec les meilleures données.

### 5. Cleanup
Suppression automatique des données anciennes ou non performantes.

## CI/CD Pipeline

### GitHub Actions
1. **Lint**: Black, Flake8, MyPy
2. **Test**: Pytest avec couverture
3. **Build**: Validation de compilation
4. **Deploy**: Déploiement automatique sur Windsurf

### Scheduled Jobs
- Learning pipeline: Hebdomadaire (lundi 3h)
- Cleanup: Quotidien via scheduler interne

## Technologies

### Backend
- Python 3.11+
- FastAPI (API REST)
- Ollama + Mistral 7B (IA)
- SQLite (stockage local)
- APScheduler (tâches planifiées)

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Query (data fetching)

## Security

- CORS configuré
- Validation Pydantic
- Sanitisation des entrées
- Logs structurés

## Performance

- Cache en mémoire (builds/teams)
- Compression des données (zlib)
- API asynchrone (asyncio)
- Lazy loading (frontend)

## Monitoring

- Health checks (API, Ollama)
- Logs structurés
- Statistiques d'apprentissage
- Métriques de couverture de code
