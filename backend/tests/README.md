# Tests - GW2Optimizer Backend

## 📋 Vue d'ensemble

Ce dossier contient la suite de tests complète pour le backend GW2Optimizer v1.2.0.

**Objectif de couverture** : ≥ 80%  
**Type de tests** : Unitaires, API, Intégration  
**Base de données** : PostgreSQL + SQLite (tests)  
**Cache** : Redis + Fallback disque

## 📁 Structure

```
tests/
├── README.md                    # Ce fichier
├── conftest.py                  # Fixtures partagées
├── test_services/               # Tests unitaires des services
│   ├── __init__.py
│   ├── test_build_service.py   # 15+ tests BuildService
│   └── test_team_service.py    # 15+ tests TeamService
├── test_api/                    # Tests des endpoints API
│   ├── __init__.py
│   ├── test_builds.py          # 20+ tests API builds
│   └── test_teams.py           # 15+ tests API teams
└── test_integration/            # Tests d'intégration
    ├── __init__.py
    ├── test_auth_flow.py       # 10+ tests authentification
    └── test_cache_flow.py      # 10+ tests cache Redis
```

## 🚀 Exécution rapide

### Tous les tests
```bash
pytest
```

### Avec couverture
```bash
pytest --cov=app --cov-report=html
```

### Par catégorie
```bash
# Tests unitaires
pytest tests/test_services/ -v

# Tests d'API
pytest tests/test_api/ -v

# Tests d'intégration
pytest tests/test_integration/ -v
```

### Utiliser les scripts
```bash
# Validation de la configuration
./scripts/validate_tests.sh

# Exécution avec options
./scripts/run_tests.sh coverage
./scripts/run_tests.sh unit
./scripts/run_tests.sh api
```

## 🔧 Configuration

### Fixtures disponibles (conftest.py)

#### Base de données
- **`db_session`** : Session async SQLAlchemy
  - SQLite en mémoire par défaut
  - PostgreSQL si `TEST_DATABASE_URL` défini
  - Isolation complète entre tests

#### Authentification
- **`test_user`** : Utilisateur de test
- **`test_superuser`** : Superutilisateur
- **`auth_headers`** : Headers JWT pour test_user
- **`superuser_auth_headers`** : Headers JWT pour superuser

#### Client HTTP
- **`client`** : AsyncClient httpx avec override de DB

#### Données de test
- **`sample_build_data`** : Données de build
- **`sample_team_data`** : Données de team

### Variables d'environnement

```bash
# Base de données de test (optionnel)
export TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test_db"

# Redis (optionnel)
export REDIS_URL="redis://localhost:6379/0"
export REDIS_ENABLED="true"

# JWT
export SECRET_KEY="test-secret-key"
export ALGORITHM="HS256"

# Mode test
export TESTING="true"
```

## 📊 Couverture actuelle

### Par module
- **Services** : ~95%
- **API** : ~90%
- **Global** : ≥80%

### Rapport de couverture
```bash
# Générer le rapport HTML
pytest --cov=app --cov-report=html

# Ouvrir dans le navigateur
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🧪 Tests par module

### BuildService (test_services/test_build_service.py)

**15+ tests couvrant** :
- ✅ Création de builds
- ✅ Récupération (propriétaire/public)
- ✅ Listage avec filtres
- ✅ Mise à jour avec permissions
- ✅ Suppression avec permissions
- ✅ Pagination et comptage

**Exemple** :
```bash
pytest tests/test_services/test_build_service.py -v
```

### TeamService (test_services/test_team_service.py)

**15+ tests couvrant** :
- ✅ Création de teams
- ✅ Gestion des slots
- ✅ Ajout/retrait de builds
- ✅ Validation des permissions
- ✅ Auto-incrémentation

**Exemple** :
```bash
pytest tests/test_services/test_team_service.py -v
```

### API Builds (test_api/test_builds.py)

**20+ tests couvrant** :
- ✅ POST /api/v1/builds
- ✅ GET /api/v1/builds
- ✅ GET /api/v1/builds/public/all
- ✅ GET /api/v1/builds/{id}
- ✅ PUT /api/v1/builds/{id}
- ✅ DELETE /api/v1/builds/{id}
- ✅ Authentification JWT
- ✅ Validation Pydantic

**Exemple** :
```bash
pytest tests/test_api/test_builds.py -v
```

### API Teams (test_api/test_teams.py)

**15+ tests couvrant** :
- ✅ Tous les endpoints teams
- ✅ Gestion des builds dans teams
- ✅ Permissions et validations

**Exemple** :
```bash
pytest tests/test_api/test_teams.py -v
```

### Authentification (test_integration/test_auth_flow.py)

**10+ tests couvrant** :
- ✅ Register → Login → Access
- ✅ Refresh token
- ✅ Logout
- ✅ Isolation des ressources
- ✅ Validation des credentials

**Exemple** :
```bash
pytest tests/test_integration/test_auth_flow.py -v
```

### Cache Redis (test_integration/test_cache_flow.py)

**10+ tests couvrant** :
- ✅ Mise en cache
- ✅ Invalidation
- ✅ Fallback disque
- ✅ TTL et expiration
- ✅ Accès concurrent

**Exemple** :
```bash
pytest tests/test_integration/test_cache_flow.py -v
```

## 🎯 Bonnes pratiques

### Écriture de tests

1. **Nommage clair** : `test_<action>_<scenario>`
2. **AAA Pattern** : Arrange, Act, Assert
3. **Isolation** : Chaque test indépendant
4. **Fixtures** : Réutiliser les fixtures communes

### Exemple de test

```python
@pytest.mark.asyncio
async def test_create_build_success(
    db_session: AsyncSession,
    test_user: UserDB,
    sample_build_data: dict
):
    # Arrange
    service = BuildService(db_session)
    build_data = BuildCreate(**sample_build_data)
    
    # Act
    result = await service.create_build(build_data, test_user)
    
    # Assert
    assert result is not None
    assert result.name == sample_build_data["name"]
    assert result.user_id == test_user.id
```

## 🔍 Dépannage

### Erreur : "fixture not found"
```bash
# Vérifier que conftest.py existe
ls tests/conftest.py

# Lister les fixtures disponibles
pytest --fixtures
```

### Erreur : "Database connection"
```bash
# Utiliser SQLite en mémoire (par défaut)
unset TEST_DATABASE_URL

# Ou vérifier PostgreSQL
pg_isready
```

### Erreur : "Redis connection"
```bash
# Désactiver Redis pour les tests
export REDIS_ENABLED=false

# Ou vérifier Redis
redis-cli ping
```

### Tests lents
```bash
# Paralléliser
pytest -n auto

# Exclure les tests lents
pytest -m "not slow"
```

## 📚 Documentation

- **Guide complet** : [docs/TESTING.md](../../docs/TESTING.md)
- **Setup CI/CD** : [docs/CI_CD_SETUP.md](../../docs/CI_CD_SETUP.md)
- **Implémentation** : [TESTS_AND_CI_IMPLEMENTATION.md](../../TESTS_AND_CI_IMPLEMENTATION.md)

## 🤝 Contribution

Lors de l'ajout de nouveaux tests :
1. Suivre la structure existante
2. Utiliser les fixtures communes
3. Maintenir la couverture ≥ 80%
4. Documenter les scénarios complexes
5. Exécuter tous les tests avant de commit

## 📞 Support

Pour toute question :
1. Consulter la documentation
2. Vérifier les exemples existants
3. Créer une issue avec le label `testing`

---

**Version** : 1.2.0  
**Dernière mise à jour** : 2024-01-20  
**Couverture** : ≥ 80%
