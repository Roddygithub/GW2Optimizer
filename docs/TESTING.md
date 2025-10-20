# Guide de test pour GW2Optimizer v1.2.0

## 📋 Table des matières

- [Introduction](#introduction)
- [Structure des tests](#structure-des-tests)
- [Installation](#installation)
- [Exécution des tests](#exécution-des-tests)
- [Couverture de code](#couverture-de-code)
- [Tests unitaires](#tests-unitaires)
- [Tests d'API](#tests-dapi)
- [Tests d'intégration](#tests-dintégration)
- [CI/CD](#cicd)
- [Dépannage](#dépannage)

## Introduction

Ce guide décrit comment exécuter et maintenir la suite de tests pour GW2Optimizer. Notre objectif est de maintenir une couverture de code **≥ 80%** avec des tests réels utilisant PostgreSQL et Redis.

## Structure des tests

```
backend/tests/
├── __init__.py
├── conftest.py                    # Fixtures partagées
├── test_services/                 # Tests unitaires des services
│   ├── __init__.py
│   ├── test_build_service.py     # Tests BuildService
│   └── test_team_service.py      # Tests TeamService
├── test_api/                      # Tests des endpoints API
│   ├── __init__.py
│   ├── test_builds.py            # Tests API builds
│   └── test_teams.py             # Tests API teams
└── test_integration/              # Tests d'intégration
    ├── __init__.py
    ├── test_auth_flow.py         # Tests flux d'authentification
    └── test_cache_flow.py        # Tests cache Redis
```

## Installation

### Prérequis

- Python 3.11+
- PostgreSQL 14+ (optionnel, SQLite utilisé par défaut pour les tests)
- Redis 6+ (optionnel, fakeredis utilisé par défaut)
- Docker (recommandé pour les services)

### Installation des dépendances

```bash
cd backend

# Installer les dépendances de production
pip install -r requirements.txt

# Installer les dépendances de développement
pip install -r requirements-dev.txt
```

### Configuration de l'environnement de test

```bash
# Copier le fichier d'exemple
cp .env.example .env.test

# Éditer .env.test avec vos paramètres de test
# Pour les tests locaux, SQLite en mémoire est utilisé par défaut
```

## Exécution des tests

### Tous les tests

```bash
cd backend
pytest
```

### Tests avec couverture

```bash
# Rapport en terminal
pytest --cov=app --cov-report=term-missing

# Rapport HTML
pytest --cov=app --cov-report=html

# Rapport XML (pour CI/CD)
pytest --cov=app --cov-report=xml

# Vérifier la couverture minimale (80%)
pytest --cov=app --cov-fail-under=80
```

### Tests par catégorie

```bash
# Tests unitaires des services
pytest tests/test_services/ -v

# Tests d'API
pytest tests/test_api/ -v

# Tests d'intégration
pytest tests/test_integration/ -v -m integration
```

### Tests spécifiques

```bash
# Un fichier de test
pytest tests/test_services/test_build_service.py -v

# Une classe de test
pytest tests/test_services/test_build_service.py::TestBuildService -v

# Un test spécifique
pytest tests/test_services/test_build_service.py::TestBuildService::test_create_build_success -v
```

### Tests avec marqueurs

```bash
# Tests unitaires uniquement
pytest -m unit

# Tests d'intégration uniquement
pytest -m integration

# Exclure les tests lents
pytest -m "not slow"
```

### Tests en parallèle

```bash
# Exécuter sur 4 processus
pytest -n 4

# Auto-détection du nombre de CPU
pytest -n auto
```

## Couverture de code

### Objectif de couverture

- **Minimum requis** : 80%
- **Objectif** : 90%+
- **Idéal** : 95%+

### Visualiser la couverture

```bash
# Générer le rapport HTML
pytest --cov=app --cov-report=html

# Ouvrir le rapport dans le navigateur
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Rapport de couverture détaillé

```bash
# Voir les lignes manquantes
pytest --cov=app --cov-report=term-missing

# Rapport par fichier
pytest --cov=app --cov-report=term:skip-covered
```

## Tests unitaires

### BuildService

Les tests couvrent :
- ✅ Création de builds
- ✅ Récupération par ID (propriétaire/public)
- ✅ Listage avec filtres (profession, game_mode, role)
- ✅ Mise à jour (autorisations)
- ✅ Suppression (autorisations)
- ✅ Comptage et pagination
- ✅ Validation des permissions

**Exemple d'exécution** :
```bash
pytest tests/test_services/test_build_service.py -v
```

### TeamService

Les tests couvrent :
- ✅ Création de teams
- ✅ Ajout/retrait de builds
- ✅ Gestion des slots
- ✅ Validation des builds (public/privé)
- ✅ Auto-incrémentation des slot_number
- ✅ Cascade delete

**Exemple d'exécution** :
```bash
pytest tests/test_services/test_team_service.py -v
```

## Tests d'API

### Endpoints Builds

Tests des endpoints :
- `POST /api/v1/builds` - Création
- `GET /api/v1/builds` - Liste utilisateur
- `GET /api/v1/builds/public/all` - Liste publique
- `GET /api/v1/builds/{id}` - Récupération
- `PUT /api/v1/builds/{id}` - Mise à jour
- `DELETE /api/v1/builds/{id}` - Suppression
- `GET /api/v1/builds/stats/count` - Statistiques

**Scénarios testés** :
- ✅ Authentification requise
- ✅ Validation des données
- ✅ Permissions propriétaire
- ✅ Accès public
- ✅ Filtres et pagination

**Exemple d'exécution** :
```bash
pytest tests/test_api/test_builds.py -v
```

### Endpoints Teams

Tests similaires pour les endpoints teams avec gestion des slots.

**Exemple d'exécution** :
```bash
pytest tests/test_api/test_teams.py -v
```

## Tests d'intégration

### Flux d'authentification

Tests du workflow complet :
1. Inscription (`POST /api/v1/auth/register`)
2. Connexion (`POST /api/v1/auth/login`)
3. Accès aux endpoints protégés
4. Refresh token
5. Logout

**Scénarios testés** :
- ✅ Workflow complet register → login → access
- ✅ Credentials invalides
- ✅ Tokens invalides
- ✅ Refresh token
- ✅ Isolation des ressources entre utilisateurs

**Exemple d'exécution** :
```bash
pytest tests/test_integration/test_auth_flow.py -v
```

### Cache Redis

Tests du système de cache :
- ✅ Mise en cache des builds/teams
- ✅ Invalidation sur update/delete
- ✅ Fallback disque si Redis indisponible
- ✅ Cache avec filtres
- ✅ TTL et expiration
- ✅ Accès concurrent

**Exemple d'exécution** :
```bash
pytest tests/test_integration/test_cache_flow.py -v
```

## CI/CD

### GitHub Actions

Le pipeline CI/CD s'exécute automatiquement sur :
- Push sur `main` ou `dev`
- Pull requests vers `main` ou `dev`

### Étapes du pipeline

1. **Lint Backend**
   - Black (formatage)
   - Flake8 (style)
   - isort (imports)
   - MyPy (types)

2. **Test Backend**
   - Services PostgreSQL et Redis
   - Tests unitaires
   - Tests d'API
   - Tests d'intégration
   - Couverture ≥ 80%

3. **Upload Coverage**
   - Rapport vers Codecov
   - Artefact HTML

### Exécution locale du pipeline

```bash
# Installer act (https://github.com/nektos/act)
brew install act  # macOS
# ou
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Exécuter le workflow localement
act -j test-backend
```

### Variables d'environnement CI

Les secrets suivants doivent être configurés dans GitHub :
- `CODECOV_TOKEN` - Token Codecov pour upload de couverture
- `DB_USER` - Utilisateur PostgreSQL (pour learning pipeline)
- `DB_PASSWORD` - Mot de passe PostgreSQL
- `DB_NAME` - Nom de la base de données
- `DATABASE_URL` - URL complète de connexion
- `REDIS_URL` - URL Redis
- `SECRET_KEY` - Clé secrète JWT

## Dépannage

### Erreurs de base de données

**Problème** : `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution** :
```bash
# Vérifier que PostgreSQL est démarré
pg_isready

# Ou utiliser SQLite pour les tests (par défaut)
export TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

### Erreurs Redis

**Problème** : `redis.exceptions.ConnectionError`

**Solution** :
```bash
# Vérifier que Redis est démarré
redis-cli ping

# Ou désactiver Redis pour les tests
export REDIS_ENABLED=false
```

### Erreurs de couverture

**Problème** : `Coverage is below 80%`

**Solution** :
```bash
# Voir les lignes non couvertes
pytest --cov=app --cov-report=term-missing

# Ajouter des tests pour les fichiers manquants
```

### Tests qui échouent de manière intermittente

**Problème** : Tests qui passent parfois et échouent parfois

**Solutions** :
1. Vérifier les dépendances entre tests
2. Utiliser des fixtures isolées
3. Éviter les sleep() - utiliser des attentes explicites
4. Vérifier les transactions de base de données

### Problèmes de fixtures

**Problème** : `fixture 'db_session' not found`

**Solution** :
```bash
# Vérifier que conftest.py est présent
ls tests/conftest.py

# Vérifier les imports
pytest --fixtures
```

### Nettoyage après les tests

```bash
# Supprimer les fichiers de cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Supprimer les rapports de couverture
rm -rf htmlcov/ .coverage coverage.xml

# Supprimer les bases de données de test
rm -f test.db
```

## Bonnes pratiques

### Écriture de tests

1. **Nommage** : `test_<action>_<scenario>`
   ```python
   def test_create_build_success()
   def test_create_build_unauthorized()
   ```

2. **AAA Pattern** : Arrange, Act, Assert
   ```python
   async def test_example():
       # Arrange
       user = await create_test_user()
       
       # Act
       result = await service.do_something(user)
       
       # Assert
       assert result is not None
   ```

3. **Isolation** : Chaque test doit être indépendant
   ```python
   @pytest_asyncio.fixture
   async def db_session():
       # Nouvelle session pour chaque test
       async with TestSessionLocal() as session:
           yield session
           await session.rollback()
   ```

4. **Fixtures** : Réutiliser les fixtures communes
   ```python
   @pytest.fixture
   def sample_build_data():
       return {"name": "Test", ...}
   ```

### Performance des tests

- Utiliser SQLite en mémoire pour les tests rapides
- Paralléliser avec `pytest-xdist`
- Marquer les tests lents avec `@pytest.mark.slow`
- Utiliser des fixtures avec scope approprié

### Maintenance

- Mettre à jour les tests lors des changements d'API
- Maintenir la couverture ≥ 80%
- Documenter les scénarios complexes
- Réviser régulièrement les tests obsolètes

## Ressources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## Support

Pour toute question ou problème :
1. Consulter cette documentation
2. Vérifier les issues GitHub existantes
3. Créer une nouvelle issue avec le label `testing`

---

**Dernière mise à jour** : 2024-01-20  
**Version** : 1.2.0  
**Couverture actuelle** : ≥ 80%
