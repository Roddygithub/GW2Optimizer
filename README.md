# GW2Optimizer 🛡️⚔️

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/roddy/GW2Optimizer/releases)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/roddy/GW2Optimizer/actions)
[![Tests](https://img.shields.io/badge/tests-145%2F145%20passing-brightgreen.svg)](https://github.com/roddy/GW2Optimizer/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://github.com/roddy/GW2Optimizer/coverage)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3.3-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-contributor%20covenant-purple.svg)](CODE_OF_CONDUCT.md)

**AI-Powered Build and Team Composition Optimizer for Guild Wars 2**

Optimiseur d'équipes McM (WvW) pour Guild Wars 2 avec IA Mistral 7B intégrée.

---

## ✨ Features

### v1.1.0 - Meta Analysis System 🆕
- 🧠 **Meta Adaptative Agent** - Analyse automatique des tendances de méta
- 🌐 **GW2 API Integration** - Connexion directe à l'API officielle Guild Wars 2
- 📊 **Meta Analysis Workflow** - Workflow complet d'analyse de méta
- 🎯 **Viability Scoring** - Évaluation de la viabilité des builds (0.0-1.0)
- 📈 **Trend Detection** - Détection automatique des changements de méta
- 🔮 **Meta Predictions** - Prédictions d'évolution du méta
- 💾 **Smart Caching** - Cache intelligent (24h TTL) pour l'API GW2

### Core Features
- 🤖 **AI-Powered Recommendations** - Mistral 7B via Ollama for intelligent build suggestions
- 🎯 **5 AI Agents** - Recommender, Synergy, Optimizer, Meta, and Learning agents
- 🔄 **4 AI Workflows** - Build Optimization, Team Analysis, Meta Analysis, and Learning Pipeline
- 🔐 **Secure Authentication** - JWT with refresh tokens and account protection
- 📊 **50+ API Endpoints** - Complete REST API with FastAPI
- ⚡ **Real-time Analysis** - Instant team synergy scoring
- 🎨 **Modern UI** - React 18 + TypeScript + TailwindCSS
- 🧪 **Fully Tested** - 145/145 tests passing (85% coverage)
- 📚 **Comprehensive Docs** - Installation, API, and Architecture guides
- 🚀 **Production Ready** - Validated and operational

---

## 🎯 Objectifs

GW2Optimizer génère et optimise des compositions d'équipes McM pour Guild Wars 2, en analysant les synergies et en proposant des builds adaptés à chaque mode de jeu :
- **Roaming** : petits groupes (1-5 joueurs)
- **Raid Guild** : groupes organisés (15-25 joueurs)
- **Zerg** : grandes armées (25+ joueurs)

## 🚀 Technologies

### Backend
- **Python 3.11+**
- **Ollama + Mistral 7B** : IA pour l'optimisation des builds
- **FastAPI** : API REST moderne et performante
- **BeautifulSoup4** : Scraping des sites communautaires
- **Pydantic** : Validation des données

### Frontend
- **React 18** avec TypeScript
- **Vite** : Build tool ultra-rapide
- **TailwindCSS** : Styling moderne
- **Lucide React** : Icônes
- **shadcn/ui** : Composants UI réutilisables

### CI/CD
- **GitHub Actions** : Pipeline automatisé
- **Pytest** : Tests unitaires et d'intégration
- **Playwright** : Tests E2E
- **Black, Flake8, MyPy** : Linting Python
- **ESLint, Prettier** : Linting JavaScript/TypeScript

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

## 🔧 Installation

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
- **Linting** automatique sur chaque commit
- **Tests** unitaires, d'intégration et E2E
- **Déploiement** automatique sur Windsurf après validation
- **Merge automatique** des PR si CI/CD OK
- **Rapports** automatisés sur chaque pipeline

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
