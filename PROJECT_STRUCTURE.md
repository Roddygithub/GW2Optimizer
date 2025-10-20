# 🏗️ Project Structure - GW2Optimizer

Architecture et organisation du projet GW2Optimizer.

---

## 📁 Structure globale

```
GW2Optimizer/
├── backend/              # Backend FastAPI
│   ├── app/             # Application principale
│   ├── tests/           # Tests unitaires
│   ├── data/            # Données et cache
│   └── scripts/         # Scripts utilitaires
├── frontend/            # Frontend React (v1.2.0)
├── docs/                # Documentation
├── release/             # Archives de releases
├── scripts/             # Scripts de déploiement
└── .github/             # GitHub Actions
```

---

## 🔧 Backend (`backend/`)

### Structure détaillée

```
backend/
├── app/
│   ├── agents/          # Agents IA
│   │   ├── base.py                    # Agent de base abstrait
│   │   ├── recommender_agent.py       # Recommandations de builds
│   │   ├── synergy_agent.py           # Analyse de synergies
│   │   ├── optimizer_agent.py         # Optimisation d'équipes
│   │   ├── meta_agent.py              # ✨ Analyse de méta (v1.1.0)
│   │   └── __init__.py
│   │
│   ├── api/             # Endpoints REST
│   │   ├── auth.py                    # Authentification
│   │   ├── builds.py                  # CRUD builds
│   │   ├── teams.py                   # CRUD équipes
│   │   ├── ai.py                      # Endpoints IA
│   │   ├── chat.py                    # Chat IA
│   │   ├── export.py                  # Export builds/teams
│   │   ├── health.py                  # Health checks
│   │   ├── learning.py                # ML pipeline
│   │   ├── scraper.py                 # Scraping communautaire
│   │   ├── meta.py                    # ✨ Meta Analysis (v1.1.0)
│   │   └── __init__.py
│   │
│   ├── core/            # Configuration et utilitaires
│   │   ├── config.py                  # Configuration app
│   │   ├── logging.py                 # Logging centralisé
│   │   ├── security.py                # Sécurité et hashing
│   │   └── __init__.py
│   │
│   ├── db/              # Base de données
│   │   ├── models.py                  # Modèles SQLAlchemy
│   │   ├── database.py                # Configuration DB
│   │   └── __init__.py
│   │
│   ├── services/        # Services métier
│   │   ├── gw2skill_parser.py         # Parser GW2Skill
│   │   ├── snowcrows_scraper.py       # Scraper Snowcrows
│   │   ├── metabattle_scraper.py      # Scraper MetaBattle
│   │   ├── hardstuck_scraper.py       # Scraper Hardstuck
│   │   ├── gw2_api_client.py          # ✨ Client API GW2 (v1.1.0)
│   │   └── __init__.py
│   │
│   ├── workflows/       # Workflows IA
│   │   ├── base.py                    # Workflow de base
│   │   ├── build_optimization_workflow.py
│   │   ├── team_analysis_workflow.py
│   │   ├── learning_workflow.py
│   │   ├── meta_analysis_workflow.py  # ✨ Workflow méta (v1.1.0)
│   │   └── __init__.py
│   │
│   ├── ai.py            # Service IA principal
│   ├── auth.py          # Authentification
│   ├── exceptions.py    # Exceptions personnalisées
│   ├── middleware.py    # Middlewares FastAPI
│   ├── main.py          # Point d'entrée FastAPI
│   └── __init__.py
│
├── tests/               # Tests unitaires
│   ├── test_agents.py
│   ├── test_workflows.py
│   ├── test_api.py
│   ├── test_meta_agent.py             # ✨ Tests Meta Agent (v1.1.0)
│   ├── test_gw2_api_client.py         # ✨ Tests GW2 API (v1.1.0)
│   ├── test_meta_analysis_workflow.py # ✨ Tests Workflow (v1.1.0)
│   └── conftest.py
│
├── data/                # Données
│   ├── cache/           # Cache temporaire
│   ├── learning/        # Données ML
│   └── local_db/        # Base SQLite
│
├── alembic/             # Migrations DB
│   ├── versions/
│   └── env.py
│
├── requirements.txt     # Dépendances Python
├── pyproject.toml       # Configuration projet
├── pytest.ini           # Configuration pytest
└── .coveragerc          # Configuration coverage
```

---

## 🎯 Modules principaux

### 1. Agents IA (`app/agents/`)

**Rôle**: Agents intelligents spécialisés utilisant Mistral via Ollama

| Agent | Description | Capacités |
|-------|-------------|-----------|
| `BaseAgent` | Classe abstraite de base | Initialisation, validation, cleanup |
| `RecommenderAgent` | Recommandations de builds | Analyse besoins, suggestions personnalisées |
| `SynergyAgent` | Analyse de synergies | Détection combos, évaluation compatibilité |
| `OptimizerAgent` | Optimisation d'équipes | Composition optimale, équilibrage rôles |
| `MetaAgent` ✨ | Analyse de méta (v1.1.0) | Tendances, viabilité, prédictions |

**Technologies**: Ollama, Mistral, asyncio

---

### 2. Workflows (`app/workflows/`)

**Rôle**: Orchestration de plusieurs agents pour tâches complexes

| Workflow | Description | Agents utilisés |
|----------|-------------|-----------------|
| `BuildOptimizationWorkflow` | Optimisation complète de build | Recommender, Synergy |
| `TeamAnalysisWorkflow` | Analyse d'équipe | Synergy, Optimizer |
| `LearningWorkflow` | Pipeline ML | Tous les agents |
| `MetaAnalysisWorkflow` ✨ | Analyse méta (v1.1.0) | MetaAgent, GW2APIClient |

**Pattern**: Chain of Responsibility + Observer

---

### 3. API REST (`app/api/`)

**Rôle**: Endpoints HTTP pour interaction avec le frontend

| Module | Endpoints | Description |
|--------|-----------|-------------|
| `auth.py` | `/api/v1/auth/*` | Authentification, tokens |
| `builds.py` | `/api/v1/builds/*` | CRUD builds |
| `teams.py` | `/api/v1/teams/*` | CRUD équipes |
| `ai.py` | `/api/v1/ai/*` | Recommandations IA |
| `chat.py` | `/api/v1/chat` | Chat conversationnel |
| `meta.py` ✨ | `/api/v1/meta/*` | Meta Analysis (v1.1.0) |

**Total**: 50+ endpoints

---

### 4. Services (`app/services/`)

**Rôle**: Services métier et intégrations externes

| Service | Description | Intégration |
|---------|-------------|-------------|
| `gw2skill_parser.py` | Parse URLs GW2Skill | GW2Skill.net |
| `snowcrows_scraper.py` | Scrape builds raid | Snowcrows.com |
| `metabattle_scraper.py` | Scrape builds WvW | MetaBattle.com |
| `hardstuck_scraper.py` | Scrape builds WvW | Hardstuck.gg |
| `gw2_api_client.py` ✨ | Client API GW2 (v1.1.0) | api.guildwars2.com |

**Technologies**: httpx, BeautifulSoup, asyncio

---

### 5. Base de données (`app/db/`)

**Rôle**: Modèles et gestion de la base de données

**Modèles**:
- `User`: Utilisateurs
- `Build`: Builds de personnages
- `TeamComposition`: Compositions d'équipes
- `TeamSlot`: Slots dans une équipe
- `TeamBuild`: Association équipe-build

**ORM**: SQLAlchemy  
**DB**: SQLite (dev), PostgreSQL (prod)

---

## 🔄 Flux de données

### 1. Création de build avec IA

```
User Request
    ↓
POST /api/v1/builds (with custom_requirements)
    ↓
RecommenderAgent.run()
    ↓
Mistral Analysis
    ↓
Build Created in DB
    ↓
Response to User
```

### 2. Analyse de méta (v1.1.0)

```
User Request
    ↓
POST /api/v1/meta/analyze
    ↓
MetaAnalysisWorkflow.run()
    ↓
├─ GW2APIClient.import_data() (optional)
├─ MetaAgent.analyze_meta()
├─ MetaAgent.detect_trends()
├─ MetaAgent.calculate_viability()
└─ MetaAgent.generate_recommendations()
    ↓
Meta Report Generated
    ↓
Response to User
```

### 3. Optimisation d'équipe

```
User Request
    ↓
POST /api/v1/teams/optimize
    ↓
TeamAnalysisWorkflow.run()
    ↓
├─ OptimizerAgent (composition)
├─ SynergyAgent (synergies)
└─ RecommenderAgent (suggestions)
    ↓
Optimal Team Created
    ↓
Response to User
```

---

## 🧪 Tests (`tests/`)

**Structure**:
```
tests/
├── test_agents.py              # Tests agents IA
├── test_workflows.py           # Tests workflows
├── test_api.py                 # Tests API endpoints
├── test_meta_agent.py          # ✨ Tests MetaAgent (15 tests)
├── test_gw2_api_client.py      # ✨ Tests GW2APIClient (12 tests)
├── test_meta_analysis_workflow.py  # ✨ Tests Workflow (18 tests)
└── conftest.py                 # Fixtures pytest
```

**Coverage**: 85-90%  
**Framework**: pytest, pytest-asyncio

---

## 📦 Dépendances principales

### Backend
- **FastAPI**: Framework web
- **SQLAlchemy**: ORM
- **Pydantic**: Validation de données
- **httpx**: Client HTTP async
- **BeautifulSoup4**: Scraping
- **pytest**: Tests

### IA
- **Ollama**: Serveur LLM local
- **Mistral**: Modèle de langage

---

## 🚀 Points d'entrée

### Développement
```bash
cd backend
uvicorn app.main:app --reload
```

### Production
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

---

## 🔐 Sécurité

**Middlewares**:
- `SecurityHeadersMiddleware`: Headers de sécurité (CSP, X-Frame-Options)
- `CorrelationIdMiddleware`: Traçabilité des requêtes
- `ProcessTimeMiddleware`: Monitoring des performances

**Authentification**:
- JWT tokens (access + refresh)
- OAuth2 avec cookies
- Hashing bcrypt

---

## 📊 Métriques

### Code
- **Lignes de code backend**: ~15,000 lignes
- **Fichiers Python**: 50+ fichiers
- **Agents IA**: 5 agents
- **Workflows**: 4 workflows
- **Endpoints API**: 50+ endpoints

### Tests
- **Tests unitaires**: 100+ tests
- **Coverage**: 85-90%
- **Tests v1.1.0**: 45 nouveaux tests

---

## 🎯 Architecture patterns

- **Clean Architecture**: Séparation des couches
- **Repository Pattern**: Accès aux données
- **Factory Pattern**: Création d'agents
- **Observer Pattern**: Workflows
- **Dependency Injection**: FastAPI

---

## 📝 Notes

- ✨ = Nouveautés v1.1.0
- Structure modulaire et extensible
- Tests complets pour chaque module
- Documentation inline (docstrings)

---

**Version**: v1.1.0  
**Dernière mise à jour**: 2025-10-20  
**Maintenu par**: Roddy
