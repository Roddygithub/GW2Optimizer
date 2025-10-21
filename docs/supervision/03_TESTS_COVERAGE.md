# 03 - Tests & Coverage

**Section**: Tests Unitaires et Couverture  
**Coverage Global**: 30.63%  
**Date**: 2025-10-21

---

## 📊 ÉTAT ACTUEL

### Résumé Global

```
Total Lines: 4,936
Covered: 1,513
Coverage: 30.63%
```

**Status**:
- 🟢 Tests GUID: 8/8 (100%)
- 🟡 Coverage global: 30.63%
- 🔴 Modules critiques: <15%

---

## ✅ TESTS VALIDÉS

### 1. Tests GUID (NOUVEAU) ✅

**Fichier**: `backend/tests/test_db_types.py`

**Coverage**: 81.48% sur `app/db/types.py`

```
✅ test_guid_creation_sqlite             PASSED
✅ test_guid_default_generation_sqlite   PASSED
✅ test_guid_query_by_uuid_sqlite        PASSED
✅ test_guid_null_handling_sqlite        PASSED
✅ test_guid_string_conversion_sqlite    PASSED
✅ test_guid_multiple_records_sqlite     PASSED
✅ test_guid_update_sqlite               PASSED
✅ test_guid_delete_sqlite               PASSED

======================== 8 passed in 2.55s ========================
```

**Points validés**:
- ✅ Création UUID SQLite
- ✅ Auto-génération default
- ✅ Requêtes par UUID
- ✅ Conversion String ↔ UUID
- ✅ Gestion NULL
- ✅ CRUD complet

### 2. Tests WebSocket McM ✅

**Fichier**: `backend/tests/test_websocket_mcm.py`

**7 tests** (état à vérifier):
1. test_websocket_health_endpoint
2. test_mcm_analytics_service
3. test_squad_recommendations
4. test_objective_tracking
5. test_battle_analytics
6. test_commander_stats
7. test_get_live_metrics

**Coverage**: 56.52% sur `app/services/mcm_analytics.py`

---

## ⚠️ TESTS EN ERREUR

### Tests Services Build (15 erreurs)

**Fichier**: `backend/tests/test_services/test_build_service.py`

**Problème**: Fixture `sample_build_data` manquante

**Tests impactés**:
- test_create_build_success
- test_create_build_with_invalid_profession
- test_get_build_by_owner
- test_get_public_build_by_other_user
- test_get_private_build_by_other_user_fails
- test_list_user_builds
- test_list_user_builds_with_profession_filter
- test_list_user_builds_with_game_mode_filter
- test_list_public_builds
- test_update_build_success
- test_update_build_unauthorized
- test_delete_build_success
- test_delete_build_unauthorized
- test_count_user_builds
- test_pagination

**Solution** (voir [Guide Reprise](./05_GUIDE_REPRISE.md)):
```python
# Dans tests/conftest.py
@pytest.fixture
def sample_build_data():
    return {
        "name": "Test Guardian Build",
        "profession": "Guardian",
        "specialization": "Firebrand",
        "game_mode": "wvw",
        "role": "support",
        "trait_lines": [...],
        "skills": [...],
        "equipment": [],
        "is_public": True,
    }
```

**Impact**: 15 tests débloqués après ajout fixture

---

## 📉 COUVERTURE PAR MODULE

### Modules Critiques (<20%)

| Module | Coverage | Priority |
|--------|----------|----------|
| `app/services/auth_service.py` | **0.00%** | 🔴 HAUTE |
| `app/services/build_service_db.py` | **15.45%** | 🔴 HAUTE |
| `app/services/team_service_db.py` | **12.43%** | 🔴 HAUTE |
| `app/services/user_service.py` | **32.50%** | 🟡 MOYENNE |
| `app/services/gw2_api_client.py` | **21.14%** | 🟡 MOYENNE |
| `app/services/synergy_analyzer.py` | **20.11%** | 🟡 MOYENNE |

### Modules Moyens (20-40%)

| Module | Coverage | Status |
|--------|----------|--------|
| `app/services/build_service.py` | 28.00% | 🟡 |
| `app/services/team_service.py` | 30.26% | 🟡 |
| `app/services/ai_service.py` | 22.77% | 🟡 |
| `app/core/security.py` | 27.93% | 🟡 |
| `app/api/websocket_mcm.py` | 29.49% | 🟡 |

### Modules Bons (>60%)

| Module | Coverage | Status |
|--------|----------|--------|
| `app/db/types.py` | **81.48%** | ✅ |
| `app/models/user.py` | **76.12%** | ✅ |
| `app/core/config.py` | **100.00%** | ✅ |
| `app/core/logging.py` | **100.00%** | ✅ |
| `app/db/models.py` | **100.00%** | ✅ |
| `app/models/build.py` | **100.00%** | ✅ |
| `app/models/team.py` | **100.00%** | ✅ |

---

## 🎯 PLAN AMÉLIORATION COVERAGE

### Objectif: 30% → 60%

**Phase 1**: Tests Services DB (Semaine 1)

**Priorité HAUTE** - +15% coverage

1. **test_auth_service.py** (nouveau)
   - test_verify_password
   - test_get_password_hash
   - test_authenticate_user
   - test_create_user
   - test_get_user_by_email
   - **Impact**: +10% coverage

2. **test_build_service_db.py** (compléter)
   - Ajouter fixture `sample_build_data`
   - 15 tests existants débloqués
   - **Impact**: +3% coverage

3. **test_team_service_db.py** (compléter)
   - Tests CRUD teams
   - Tests permissions
   - **Impact**: +2% coverage

**Phase 2**: Tests API Endpoints (Semaine 2)

**Priorité MOYENNE** - +10% coverage

4. **test_api_builds.py** (nouveau)
   - POST /builds
   - GET /builds/{id}
   - PUT /builds/{id}
   - DELETE /builds/{id}
   - **Impact**: +5% coverage

5. **test_api_teams.py** (nouveau)
   - CRUD teams via API
   - **Impact**: +3% coverage

6. **test_api_auth.py** (compléter)
   - Login/logout
   - Token refresh
   - **Impact**: +2% coverage

**Phase 3**: Tests Intégration (Semaine 3)

**Priorité BASSE** - +5% coverage

7. **test_workflows.py** (nouveau)
   - BuildOptimizationWorkflow
   - MetaAnalysisWorkflow
   - **Impact**: +3% coverage

8. **test_agents.py** (nouveau)
   - RecommenderAgent
   - **Impact**: +2% coverage

---

## 🧪 FIXTURES EXISTANTES

### Fixtures Globales (conftest.py)

```python
@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Setup test database (SQLite in-memory)."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(setup_database):
    """Create async database session for tests."""
    async with TestingSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> UserDB:
    """Create test user."""
    user = UserDB(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Create test HTTP client."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def auth_headers(test_user: UserDB):
    """Generate auth headers with JWT token."""
    token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {token}"}
```

### Fixtures Manquantes

**À créer**:

```python
@pytest.fixture
def sample_build_data():
    """Sample build data for testing."""
    return {
        "name": "Test Guardian Firebrand",
        "profession": "Guardian",
        "specialization": "Firebrand",
        "game_mode": "wvw",
        "role": "support",
        "trait_lines": [
            {"id": 1, "traits": [1950, 1942, 1945]},
            {"id": 42, "traits": [2101, 2159, 2154]},
            {"id": 62, "traits": [2075, 2103, 2083]},
        ],
        "skills": [
            {"slot": "heal", "id": 9153},
            {"slot": "utility1", "id": 9246},
            {"slot": "utility2", "id": 9153},
            {"slot": "utility3", "id": 9175},
            {"slot": "elite", "id": 43123},
        ],
        "equipment": [],
        "synergies": ["might", "quickness", "stability"],
        "counters": [],
        "is_public": True,
        "description": "Test build for unit tests",
    }

@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "name": "Test WvW Zerg Team",
        "game_mode": "wvw",
        "description": "Test team composition",
        "is_public": True,
    }

@pytest_asyncio.fixture
async def test_build(db_session: AsyncSession, test_user: UserDB, sample_build_data):
    """Create test build in database."""
    build = BuildDB(
        **sample_build_data,
        user_id=test_user.id
    )
    db_session.add(build)
    await db_session.commit()
    await db_session.refresh(build)
    return build
```

---

## 📋 CHECKLIST TESTS

### Tests Unitaires Services

- [x] **test_db_types.py** - GUID (8/8) ✅
- [ ] **test_auth_service.py** - Authentication
- [ ] **test_build_service_db.py** - Builds DB (15 en attente)
- [ ] **test_team_service_db.py** - Teams DB
- [ ] **test_user_service.py** - Users
- [ ] **test_gw2_api_client.py** - GW2 API
- [ ] **test_synergy_analyzer.py** - Synergies

### Tests API Endpoints

- [ ] **test_api_auth.py** - Auth endpoints
- [ ] **test_api_builds.py** - Builds CRUD
- [ ] **test_api_teams.py** - Teams CRUD
- [ ] **test_api_websocket.py** - WebSocket McM

### Tests Intégration

- [ ] **test_workflows.py** - Workflows multi-agents
- [ ] **test_agents.py** - IA agents
- [ ] **test_e2e.py** - End-to-end

---

## 🔬 OUTILS DE TEST

### Pytest Configuration

**pytest.ini**:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=xml
    --cov-report=term
    -v
```

### Coverage Configuration

**.coveragerc**:
```ini
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod
```

---

## 🎯 OBJECTIFS COURT TERME

### Semaine 1 (Immédiat)

1. ✅ **Ajouter fixture `sample_build_data`**
   - Débloquer 15 tests
   - Impact: +3% coverage

2. ⏳ **Tests auth_service**
   - 10 nouveaux tests
   - Impact: +10% coverage

3. ⏳ **Compléter test_build_service_db**
   - Valider 15 tests existants
   - Ajouter tests edge cases

**Objectif Coverage**: 30% → 43%

### Semaine 2-3 (Court terme)

4. Tests API endpoints
5. Tests user_service
6. Tests team_service_db

**Objectif Coverage**: 43% → 55%

### Mois 1 (Moyen terme)

7. Tests workflows
8. Tests agents IA
9. Tests intégration

**Objectif Coverage**: 55% → 60%

---

## 📊 COMMANDES UTILES

### Exécuter Tests

```bash
# Tous les tests
cd backend
pytest

# Tests spécifiques
pytest tests/test_db_types.py -v
pytest tests/test_services/ -v

# Avec coverage
pytest --cov=app --cov-report=html

# Tests rapides (sans coverage)
pytest -x --ff
```

### Générer Rapport Coverage

```bash
# HTML (navigable)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Terminal
pytest --cov=app --cov-report=term-missing

# XML (pour CI/CD)
pytest --cov=app --cov-report=xml
```

### Coverage Modules Spécifiques

```bash
# Coverage d'un module
pytest --cov=app.services.build_service_db --cov-report=term

# Coverage avec détails manquants
pytest --cov=app --cov-report=term-missing
```

---

[← Architecture](./02_ARCHITECTURE.md) | [Index](./00_INDEX.md) | [Roadmap →](./04_ROADMAP.md)
