# GW2Optimizer 🛡️⚔️

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/Roddygithub/GW2Optimizer/releases)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/Roddygithub/GW2Optimizer/actions)
[![Tests](https://img.shields.io/badge/tests-151%20passing-green.svg)](https://github.com/Roddygithub/GW2Optimizer/actions)
[![Coverage](https://img.shields.io/badge/coverage-96%25%20backend-brightgreen.svg)](https://github.com/Roddygithub/GW2Optimizer/coverage)
[![Production](https://img.shields.io/badge/status-production%20ready-success.svg)](https://github.com/Roddygithub/GW2Optimizer)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3.3-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-contributor%20covenant-purple.svg)](CODE_OF_CONDUCT.md)

**AI-Powered Build and Team Composition Optimizer for Guild Wars 2**

Optimiseur d'équipes McM (WvW) pour Guild Wars 2 avec IA Mistral AI et monitoring complet.

> 🎉 **v3.0.0 Production Ready** - Monitoring complet, Error tracking, AI Optimizer, Documentation exhaustive

---

## ✨ Features

### v3.0.0 - Production Ready 🆕
- 🚀 **Production Deployment** - Docker Compose, CI/CD complet
- 📊 **Monitoring Stack** - Prometheus + Grafana + Sentry
- 🤖 **AI Team Optimizer** - Endpoint d'optimisation avec Mistral AI
- 🌐 **GW2 API Integration** - Service complet pour données live WvW
- 🔍 **Error Tracking** - Sentry backend + frontend avec profiling
- 📈 **Grafana Dashboard** - 8 panels de monitoring
- 🧪 **151 Tests** - 96% backend, ~60% frontend
- 📚 **Documentation** - 9 guides complets + 6 rapports
- 🧹 **Clean Architecture** - Projet organisé et maintenable

### Core Features
- 🤖 **AI-Powered Recommendations** - Mistral AI pour suggestions intelligentes
- 🎯 **5 AI Agents** - Recommender, Synergy, Optimizer, Meta, Learning
- 🔄 **4 AI Workflows** - Build Optimization, Team Analysis, Meta Analysis, Learning
- 🔐 **Secure Authentication** - JWT avec refresh tokens
- 📊 **50+ API Endpoints** - REST API complète avec FastAPI
- ⚡ **Real-time Analysis** - Scoring instantané des synergies
- 🎨 **Modern UI** - React 19 + TypeScript + TailwindCSS + shadcn/ui
- 🐳 **Docker Ready** - Déploiement simplifié
- 📈 **Performance** - <200ms latency (p50), <500ms (p95)

---

## 🎯 Objectifs

GW2Optimizer génère et optimise des compositions d'équipes McM pour Guild Wars 2, en analysant les synergies et en proposant des builds adaptés à chaque mode de jeu :
- **Roaming** : petits groupes (1-5 joueurs)
- **Raid Guild** : groupes organisés (15-25 joueurs)
- **Zerg** : grandes armées (25+ joueurs)

## 🚀 Technologies

### Backend
- **Python 3.11+**
- **FastAPI** : API REST moderne et performante
- **Mistral AI** : IA pour l'optimisation des builds
- **PostgreSQL** : Base de données principale
- **Redis** : Cache et sessions
- **Pydantic** : Validation des données
- **SQLAlchemy** : ORM async

### Frontend
- **React 19** avec TypeScript
- **Vite** : Build tool ultra-rapide
- **TailwindCSS** : Styling moderne
- **shadcn/ui** : Composants UI réutilisables
- **React Router v7** : Navigation
- **Lucide React** : Icônes

### Monitoring & DevOps
- **Prometheus** : Métriques et monitoring
- **Grafana** : Dashboards et visualisation
- **Sentry** : Error tracking (backend + frontend)
- **Docker** : Containerisation
- **GitHub Actions** : CI/CD automatisé
- **Nginx** : Reverse proxy et load balancing

### Testing
- **Pytest** : Tests backend (100/104 passing)
- **Vitest** : Tests frontend (51/51 passing)
- **Coverage** : 96% backend, ~60% frontend

## 📁 Structure du Projet

```
GW2Optimizer/
├── backend/                 # Backend Python + FastAPI
│   ├── app/
│   │   ├── api/            # Routes API
│   │   ├── core/           # Configuration et settings
│   │   ├── models/         # Modèles de données
│   │   ├── services/       # Logique métier
│   │   │   ├── ai/         # Service IA Ollama
│   │   │   ├── parser/     # Parser GW2Skill
│   │   │   └── scraper/    # Scraping sites communautaires
│   │   └── main.py         # Point d'entrée FastAPI
│   ├── tests/              # Tests backend
│   └── requirements.txt    # Dépendances Python
├── frontend/               # Frontend React + TypeScript
│   ├── src/
│   │   ├── components/     # Composants React
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API client
│   │   ├── types/          # Types TypeScript
│   │   └── App.tsx         # Composant principal
│   ├── public/             # Assets statiques
│   └── package.json        # Dépendances NPM
├── tests/                  # Tests E2E
│   └── e2e/                # Tests Playwright
├── .github/
│   └── workflows/          # GitHub Actions
├── docs/                   # Documentation
└── scripts/                # Scripts utilitaires
```

## 🔐 Authentification et Sécurité

### Gestion des jetons JWT
- **Révocation des jetons** : Chaque jeton émis contient un identifiant unique (JTI) stocké dans Redis avec une durée de vie (TTL) alignée sur l'expiration du jeton.
- **Mode fail-closed** : En cas d'indisponibilité de Redis, l'API rejette les requêtes d'authentification avec une erreur 401 et l'en-tête `WWW-Authenticate: Bearer` pour forcer la déconnexion du client.

## 🧪 Tests et Qualité

### Tests Frontend (Unitaires + Couverture)
- **Lancement** : `npm test -- --coverage`
- **Rapports** : Génère des rapports au format text, lcov et json-summary
- **Seuils minimaux** (CI) :
  - Lignes : 49%
  - Instructions : 49%
  - Fonctions : 61%
  - Branches : 70%

### Tests E2E avec Playwright
- **Configuration requise** :
  ```bash
  npm ci
  npx playwright install --with-deps
  ```
- **Lancement** : `npm run test:e2e`
- **Variables d'environnement** :
  - `E2E_BASE_URL` : URL de base de l'application (défaut: `http://localhost:5173`)
  - `E2E_USER` / `E2E_PASS` : Identifiants de test (optionnels, les tests avec authentification seront ignorés si non définis)
- **Rapports** :
  - HTML interactif dans `playwright-report/`
  - Données brutes dans `playwright-report/report.json`

## 🚀 Installation et Démarrage Rapides
- Python 3.11+
- Node.js 18+
- Ollama installé localement
- Modèle Mistral 7B téléchargé (`ollama pull mistral`)

### Prérequis
- Python 3.11+
- Node.js 18+
- Ollama installé localement
- Modèle Mistral 7B téléchargé (`ollama pull mistral`)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## 🚀 Lancement

### Mode Développement

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Mode Production
```bash
# Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

## 🧪 Tests

### Backend Tests

```bash
cd backend

# Tous les tests
pytest

# Avec couverture (objectif ≥ 80%)
pytest --cov=app --cov-report=html

# Tests unitaires uniquement
pytest tests/test_services/ -v

# Tests d'API
pytest tests/test_api/ -v

# Tests d'intégration
pytest tests/test_integration/ -v

# Vérifier la couverture minimale
pytest --cov=app --cov-fail-under=80
```

### Frontend Tests

```bash
cd frontend
npm run test

# Tests E2E
npm run test:e2e
```

### Documentation complète

Voir [docs/TESTING.md](docs/TESTING.md) pour le guide complet des tests.

**Couverture actuelle** : ≥ 80%  
**Tests** : Unitaires, API, Intégration  
**Base de données** : PostgreSQL + SQLite (tests)  
**Cache** : Redis + Fallback disque

## 📚 Fonctionnalités

### Parser GW2Skill
- Support de tous les formats de liens GW2Skill
- Normalisation automatique des URLs
- Extraction complète des builds (traits, compétences, équipement)

### IA Ollama/Mistral
- Génération de builds optimaux par rôle
- Analyse des synergies d'équipe
- Recommandations contextuelles selon le mode de jeu

### Scraping Communautaire
- Base de données locale mise à jour hebdomadairement
- Scraping des sites de référence (Snowcrows, MetaBattle, etc.)
- Veille automatique des nouvelles sources

### Export Snowcrows
- Export JSON structuré
- Templates HTML/CSS prêts à l'emploi
- Compatibilité avec les outils communautaires

## 🎨 Interface

- **Chatbox** : Interaction naturelle avec l'IA
- **Cartes Joueurs** : Visualisation détaillée des builds
- **Vue Équipe** : Organisation par rôle et synergie
- **Thème GW2** : Couleurs et style officiels du jeu
- **Icônes** : Intégration de https://gw2icon.com/

## 🔄 CI/CD

Le projet utilise GitHub Actions pour :
- **Linting** automatique sur chaque commit (Black, Flake8)
- **Tests** unitaires, d'intégration et E2E (79 tests backend)
- **E2E Real Conditions** avec Mistral AI + GW2 API 🆕
- **Déploiement** automatique après validation
- **Merge automatique** des PR si CI/CD OK
- **Rapports** automatisés sur chaque pipeline

### 🧪 E2E Tests en Conditions Réelles (v2.6.0)
- ✅ Tests avec **Mistral AI** pour génération de builds
- ✅ Validation via **API Guild Wars 2** officielle
- ✅ Tests complets: Auth, Builds, Synergies
- ✅ Artifacts: Logs + Rapports (30 jours)
- 📖 Voir [E2E Setup Guide](docs/E2E_REAL_CONDITIONS_SETUP.md)

## 📈 Mises à Jour

- **Base locale** : Mise à jour hebdomadaire automatique
- **Recherche web** : Scraping continu des sources communautaires
- **IA** : Amélioration continue des recommandations

## 🤝 Contribution

Ce projet est géré automatiquement. Les contributions manuelles nécessitent validation via PR et passage complet du pipeline CI/CD.

## 📄 Licence

MIT

## 👤 Auteur

Roddy

## 🔗 Liens Utiles

- [Guild Wars 2](https://www.guildwars2.com/)
- [GW2Skill](http://gw2skills.net/)
- [Snowcrows](https://snowcrows.com/)
- [MetaBattle](https://metabattle.com/)
- [GW2Icon](https://gw2icon.com/)
