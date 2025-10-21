# 05 - Guide Reprise Développement

**Section**: Guide Pratique de Reprise  
**Date**: 2025-10-21  
**Pour**: Claude (développeur Windsurf)

---

## 🚀 DÉMARRAGE RAPIDE

### Reprendre le Projet

**Simple**: Dire à Claude:

> "Je reprends GW2Optimizer où nous l'avons laissé"

Les **mémoires Cascade** seront automatiquement chargées avec:
- ✅ Solution UUID complète
- ✅ État exact du projet
- ✅ Prochaines étapes prioritaires

---

## ✅ VÉRIFICATIONS INITIALES

### 1. Vérifier Solution UUID

```bash
cd /home/roddy/GW2Optimizer/backend

# Tests GUID (doivent passer 8/8)
python -m pytest tests/test_db_types.py -v
```

**Résultat attendu**:
```
✅ 8 passed in 2.55s
Coverage: 81.48% on app/db/types.py
```

### 2. Vérifier Imports

```bash
# Tester imports Python
python -c "
from app.db.models import UserDB
from app.db.types import GUID
print('✅ Imports OK')
"
```

### 3. État Tests Services

```bash
# Voir tests en erreur
python -m pytest tests/test_services/test_build_service.py -v
```

**Résultat actuel**:
```
15 ERRORS - fixture 'sample_build_data' not found
```

**C'est normal** - prochaine étape est d'ajouter cette fixture

---

## 🔧 PROCHAINE TÂCHE (1h)

### Ajouter Fixture `sample_build_data`

**Objectif**: Débloquer 15 tests services

#### Option 1: Dans `conftest.py` (recommandé)

**Fichier**: `backend/tests/conftest.py`

**Ajouter après les fixtures existantes**:

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
        "description": "Test build for unit tests",
        
        # Trait lines (3 specializations)
        "trait_lines": [
            {
                "id": 1,  # Zeal
                "traits": [1950, 1942, 1945]
            },
            {
                "id": 42,  # Radiance
                "traits": [2101, 2159, 2154]
            },
            {
                "id": 62,  # Firebrand
                "traits": [2075, 2103, 2083]
            },
        ],
        
        # Skills (heal, 3 utilities, elite)
        "skills": [
            {"slot": "heal", "id": 9153, "name": "Shelter"},
            {"slot": "utility1", "id": 9246, "name": "Mantra of Solace"},
            {"slot": "utility2", "id": 9153, "name": "Mantra of Lore"},
            {"slot": "utility3", "id": 9175, "name": "Mantra of Flame"},
            {"slot": "elite", "id": 43123, "name": "Feel My Wrath"},
        ],
        
        # Equipment (empty for now)
        "equipment": [],
        
        # Gameplay info
        "synergies": ["might", "quickness", "stability", "aegis"],
        "counters": ["conditions", "boon_strip"],
        
        # Tags
        "tags": ["wvw", "support", "firebrand", "quickness"],
        
        # Visibility
        "is_public": True,
    }
```

#### Option 2: Fichier dédié fixtures

**Créer**: `backend/tests/fixtures/builds.py`

```python
import pytest

@pytest.fixture
def sample_build_data():
    """Sample build data for testing."""
    return {...}  # Same as above

@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "name": "Test WvW Zerg Team",
        "game_mode": "wvw",
        "description": "Test team composition for WvW",
        "is_public": True,
    }

@pytest.fixture
async def test_build(db_session, test_user, sample_build_data):
    """Create test build in database."""
    from app.models.build import BuildDB
    
    build = BuildDB(
        **sample_build_data,
        user_id=test_user.id
    )
    db_session.add(build)
    await db_session.commit()
    await db_session.refresh(build)
    return build
```

**Puis dans `conftest.py`**:
```python
# Import fixtures
pytest_plugins = ["tests.fixtures.builds"]
```

### Validation

```bash
# Après ajout fixture
cd backend
python -m pytest tests/test_services/test_build_service.py -v

# Résultat attendu
# 15 passed (ou quelques failures normaux)
# AUCUNE ERREUR "fixture not found"
```

---

## 🗄️ MIGRATION ALEMBIC

### Préparer PostgreSQL (Local)

#### Option 1: Docker (Recommandé)

```bash
# Lancer PostgreSQL en Docker
docker run -d \
  --name gw2opt-postgres \
  -e POSTGRES_PASSWORD=gw2secret \
  -e POSTGRES_DB=gw2optimizer \
  -p 5432:5432 \
  postgres:15-alpine

# Vérifier connexion
docker exec -it gw2opt-postgres psql -U postgres -d gw2optimizer -c "\dt"
```

#### Option 2: PostgreSQL système

```bash
# Installer PostgreSQL (Arch Linux)
sudo pacman -S postgresql

# Initialiser
sudo -u postgres initdb -D /var/lib/postgres/data

# Démarrer service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Créer DB
sudo -u postgres createdb gw2optimizer
sudo -u postgres psql -c "CREATE USER gw2user WITH PASSWORD 'gw2pass';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE gw2optimizer TO gw2user;"
```

### Configuration Alembic

**Fichier**: `backend/alembic/env.py`

**Vérifier/Modifier**:
```python
# Line ~20
from app.db.base_class import Base
from app.db.models import UserDB, LoginHistory  # Import all models
from app.models.build import BuildDB
from app.models.team import TeamCompositionDB, TeamSlotDB

# Line ~40
target_metadata = Base.metadata

# Line ~60
def get_url():
    return os.getenv(
        "DATABASE_URL",
        "postgresql://gw2user:gw2pass@localhost/gw2optimizer"
    )
```

### Créer Migration

```bash
cd backend

# Créer migration initiale
alembic revision --autogenerate -m "Initial schema with GUID type and relationships"

# Vérifier fichier généré
ls alembic/versions/
# Ex: 001_initial_schema_with_guid_type.py

# Examiner migration
cat alembic/versions/001_*.py
```

**Vérifier que la migration contient**:
- ✅ Table `users` avec `id UUID PRIMARY KEY`
- ✅ Table `builds` avec `user_id` foreign key
- ✅ Table `team_compositions` avec relations
- ✅ Indexes sur colonnes clés

### Appliquer Migration

```bash
# Appliquer en PostgreSQL
DATABASE_URL=postgresql://gw2user:gw2pass@localhost/gw2optimizer \
alembic upgrade head

# Vérifier tables créées
DATABASE_URL=postgresql://gw2user:gw2pass@localhost/gw2optimizer \
python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('postgresql://gw2user:gw2pass@localhost/gw2optimizer')
inspector = inspect(engine)
tables = inspector.get_table_names()
print('✅ Tables créées:', tables)
"
```

### Tester avec PostgreSQL

```bash
# Lancer tests avec PostgreSQL
DATABASE_URL=postgresql://gw2user:gw2pass@localhost/gw2optimizer \
pytest tests/test_db_types.py -v

# Résultat: Tests doivent passer (GUID fonctionne aussi avec PostgreSQL)
```

---

## 🧪 TESTS - WORKFLOW COMPLET

### Workflow Quotidien

```bash
cd /home/roddy/GW2Optimizer/backend

# 1. Activer env virtuel (si utilisé)
# source venv/bin/activate

# 2. Lancer tous tests
pytest

# 3. Tests spécifiques avec coverage
pytest tests/test_db_types.py --cov=app.db.types --cov-report=term

# 4. Tests services (après ajout fixtures)
pytest tests/test_services/ -v

# 5. Voir coverage global
pytest --cov=app --cov-report=html
open htmlcov/index.html  # Ouvre rapport dans navigateur
```

### Tests Rapides (Dev)

```bash
# Arrêter au premier échec
pytest -x

# Réexécuter derniers échecs
pytest --lf

# Réexécuter échecs + tests qui ont changé
pytest --ff

# Tests d'un fichier spécifique
pytest tests/test_db_types.py::test_guid_creation_sqlite -v

# Verbose + stdout
pytest tests/test_db_types.py -vv -s
```

### CI/CD Simulation

```bash
# Comme CI/CD GitHub Actions
pytest --cov=app --cov-report=xml --cov-report=term -v

# Vérifier minimum coverage (ex: 30%)
coverage report --fail-under=30
```

---

## 🐳 DOCKER - DÉVELOPPEMENT

### Build Image

```bash
cd /home/roddy/GW2Optimizer

# Build backend
docker build -t gw2optimizer-backend:dev ./backend

# Vérifier image
docker images | grep gw2optimizer
```

### Run Container

```bash
# Lancer backend
docker run -d \
  --name gw2opt-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host.docker.internal/gw2opt \
  gw2optimizer-backend:dev

# Voir logs
docker logs -f gw2opt-backend

# Accéder API
curl http://localhost:8000/api/v1/health

# Arrêter
docker stop gw2opt-backend
docker rm gw2opt-backend
```

### Docker Compose (Stack complet)

```bash
# Lancer stack (backend + postgres + redis)
docker-compose up -d

# Voir logs
docker-compose logs -f

# Arrêter
docker-compose down

# Rebuild
docker-compose up -d --build
```

---

## 📝 CRÉER NOUVEAUX TESTS

### Template Test Service

**Fichier**: `tests/test_services/test_NEW_service.py`

```python
"""Tests for NEW service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.NEW_service import NEWService
from app.db.models import UserDB


@pytest.mark.asyncio
class TestNEWService:
    """Test suite for NEW service."""

    async def test_create_NEW(self, db_session: AsyncSession, test_user: UserDB):
        """Test creating NEW item."""
        service = NEWService(db_session)
        
        data = {...}  # Your test data
        
        result = await service.create(data, test_user)
        
        assert result is not None
        assert result.name == data["name"]
        assert result.user_id == test_user.id
    
    async def test_get_NEW_by_id(self, db_session: AsyncSession, test_user: UserDB):
        """Test getting NEW by ID."""
        service = NEWService(db_session)
        
        # Create first
        created = await service.create({...}, test_user)
        
        # Get
        result = await service.get(created.id)
        
        assert result is not None
        assert result.id == created.id
```

### Template Test API

**Fichier**: `tests/test_api/test_NEW_api.py`

```python
"""Tests for NEW API endpoints."""

import pytest
from httpx import AsyncClient

from app.db.models import UserDB


@pytest.mark.asyncio
class TestNEWAPI:
    """Test suite for NEW API."""

    async def test_create_NEW_endpoint(
        self,
        client: AsyncClient,
        test_user: UserDB,
        auth_headers: dict
    ):
        """Test POST /api/v1/NEW"""
        
        data = {...}
        
        response = await client.post(
            "/api/v1/NEW",
            json=data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == data["name"]
    
    async def test_get_NEW_endpoint(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test GET /api/v1/NEW/{id}"""
        
        # Create first
        create_response = await client.post("/api/v1/NEW", json={...}, headers=auth_headers)
        created_id = create_response.json()["id"]
        
        # Get
        response = await client.get(f"/api/v1/NEW/{created_id}", headers=auth_headers)
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == created_id
```

---

## 🔍 DEBUGGING

### Logs Structurés

```python
# Dans code
from app.core.logging import logger

logger.info("Processing build", extra={"build_id": build_id, "user_id": user.id})
logger.error("Failed to save build", exc_info=True, extra={"build_id": build_id})
```

### IPython Debug

```python
# Dans code où bug
import ipdb; ipdb.set_trace()

# Ou avec breakpoint() (Python 3.7+)
breakpoint()
```

### Tests avec Debug

```bash
# Lancer avec débug output
pytest tests/test_db_types.py -vv -s

# Avec IPython si échec
pytest tests/test_db_types.py --pdb

# Trace complète erreurs
pytest tests/test_db_types.py --tb=long
```

---

## 📚 RESSOURCES UTILES

### Documentation

- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Pytest**: https://docs.pytest.org/
- **GW2 API**: https://wiki.guildwars2.com/wiki/API:Main

### Commandes Git

```bash
# Voir dernier commit
git log -1

# Status
git status

# Diff non staged
git diff

# Commit rapide
git add -A
git commit -m "feat: Add NEW feature"
git push origin main

# Créer branche feature
git checkout -b feature/new-agents
git push -u origin feature/new-agents
```

### Variables Environnement

**Fichier**: `backend/.env`

```bash
# Database
DATABASE_URL=postgresql://gw2user:gw2pass@localhost/gw2optimizer
# Ou SQLite pour tests
# DATABASE_URL=sqlite+aiosqlite:///./test.db

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

---

## 🎯 CHECKLIST SESSION

### Avant de Commencer

- [ ] Vérifier tests GUID (8/8 passing)
- [ ] Git status clean
- [ ] Environnement virtuel activé (si utilisé)
- [ ] PostgreSQL running (si migration)

### Pendant Développement

- [ ] Tests passent localement
- [ ] Coverage maintenu/amélioré
- [ ] Black formatting appliqué
- [ ] Commits réguliers

### Avant de Push

- [ ] `pytest` - tous tests passent
- [ ] `black backend/` - code formaté
- [ ] `git status` - vérifier fichiers
- [ ] Commit message clair
- [ ] Push vers GitHub

### Fin Session

- [ ] Créer/update mémoire si nécessaire
- [ ] Documenter changements importants
- [ ] Noter prochaines tâches

---

## 🆘 PROBLÈMES COURANTS

### "fixture not found"

**Solution**: Ajouter fixture dans `conftest.py` ou importer module fixtures

### "ImportError: cannot import name X"

**Solution**: Vérifier imports circulaires, utiliser `TYPE_CHECKING`

### "CompileError: can't render UUID"

**Solution**: Utiliser `GUID()` de `app.db.types`, pas `UUID()` de PostgreSQL

### Tests SQLite lents

**Solution**: Utiliser in-memory DB: `sqlite+aiosqlite:///:memory:`

### PostgreSQL connexion refusée

**Solution**: 
```bash
# Vérifier PostgreSQL running
sudo systemctl status postgresql

# Ou Docker
docker ps | grep postgres
```

---

[← Roadmap](./04_ROADMAP.md) | [Index](./00_INDEX.md)
