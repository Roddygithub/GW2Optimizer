# 🔧 CORRECTIONS DÉTAILLÉES - GW2Optimizer

**Date**: 20 Octobre 2025  
**Type**: Guide de corrections pas-à-pas

---

## 🔴 PRIORITÉ CRITIQUE - À FAIRE MAINTENANT

### 1. Corriger Fixtures Tests (30 minutes)

#### Problème
Les tests utilisent `test_user` comme `dict` mais devraient utiliser un objet `User` SQLAlchemy.

#### Fichier: `tests/conftest.py`

**AVANT**:
```python
@pytest.fixture
async def test_user(db: AsyncSession) -> dict:
    """Create a test user."""
    user_service = UserService(db)
    user = await user_service.create(UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123"
    ))
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "password": "testpassword123"  # Plain password
    }
```

**APRÈS**:
```python
@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user_service = UserService(db)
    user = await user_service.create(UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123"
    ))
    # Store plain password as attribute for testing
    user._plain_password = "testpassword123"
    return user
```

#### Fichier: `tests/test_api/test_auth.py` (et similaires)

**AVANT**:
```python
async def test_login_success(client: AsyncClient, test_user: dict):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user['email'], "password": test_user['password']},
    )
```

**APRÈS**:
```python
async def test_login_success(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": test_user.email, "password": test_user._plain_password},
    )
```

#### Impact
- ✅ Tests plus robustes
- ✅ Typage correct
- ✅ Cohérence avec les modèles SQLAlchemy

---

### 2. Supprimer Fichiers Dupliqués (5 minutes)

#### Fichiers à Supprimer
```bash
# Ancien service IA dupliqué
rm backend/app/ai_service.py

# Fichiers frontend mal placés (après déplacement)
rm backend/app/core/LoginPage.tsx
rm backend/app/core/RegisterPage.tsx
rm backend/app/core/App.tsx
rm backend/app/core/api.ts
rm backend/app/DashboardPage.tsx
rm backend/app/AIRecommender.tsx
rm backend/app/TeamAnalyzer.tsx
```

#### Vérifier Imports
Après suppression, vérifier que tous les imports pointent vers `services/ai_service.py`:
```python
# Dans api/ai.py
from app.services.ai_service import AIService  # ✅ Correct
```

---

### 3. Créer Endpoints Workflows IA (1 heure)

#### Fichier: `backend/app/api/ai.py`

**Ajouter**:
```python
@router.post(
    "/optimize-team",
    response_model=Dict[str, Any],
    summary="Optimize Team Composition",
    dependencies=[Depends(get_current_active_user)],
)
async def optimize_team(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Optimize a team composition using OptimizerAgent."""
    ai_service = AIService()
    try:
        result = await ai_service.run_agent("optimizer", request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post(
    "/workflow/build-optimization",
    response_model=Dict[str, Any],
    summary="Execute Build Optimization Workflow",
    dependencies=[Depends(get_current_active_user)],
)
async def execute_build_optimization(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute the complete build optimization workflow."""
    ai_service = AIService()
    try:
        result = await ai_service.execute_workflow("build_optimization", request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

@router.post(
    "/workflow/team-analysis",
    response_model=Dict[str, Any],
    summary="Execute Team Analysis Workflow",
    dependencies=[Depends(get_current_active_user)],
)
async def execute_team_analysis(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute the complete team analysis workflow."""
    ai_service = AIService()
    try:
        result = await ai_service.execute_workflow("team_analysis", request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
```

---

## 🟡 PRIORITÉ MOYENNE - CETTE SEMAINE

### 4. Créer Structure Frontend (2-3 heures)

#### Étape 1: Créer structure de dossiers
```bash
mkdir -p frontend/src/{components,pages,services,hooks,utils,styles,contexts}
mkdir -p frontend/src/components/{Auth,Build,Team,Chat,Common,AI}
mkdir -p frontend/public/icons
```

#### Étape 2: Créer `package.json`
```json
{
  "name": "gw2optimizer-frontend",
  "version": "1.2.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.16.0",
    "axios": "^1.5.0",
    "lucide-react": "^0.263.0",
    "@tanstack/react-query": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "autoprefixer": "^10.4.15",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "postcss": "^8.4.28",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}
```

#### Étape 3: Déplacer composants existants
```bash
# Déplacer depuis backend/app/ vers frontend/src/
mv backend/app/core/LoginPage.tsx frontend/src/pages/
mv backend/app/core/RegisterPage.tsx frontend/src/pages/
mv backend/app/DashboardPage.tsx frontend/src/pages/
mv backend/app/AIRecommender.tsx frontend/src/components/AI/
mv backend/app/TeamAnalyzer.tsx frontend/src/components/Team/
mv backend/app/core/api.ts frontend/src/services/
mv backend/app/core/App.tsx frontend/src/
```

#### Étape 4: Mettre à jour imports
Dans chaque fichier déplacé, mettre à jour les imports relatifs.

---

### 5. Créer Tests Agents IA (1 heure)

#### Fichier: `tests/test_agents.py`

```python
"""Tests for AI Agents."""

import pytest
from app.agents.recommender_agent import RecommenderAgent
from app.agents.synergy_agent import SynergyAgent
from app.agents.optimizer_agent import OptimizerAgent

pytestmark = pytest.mark.asyncio


class TestRecommenderAgent:
    """Tests for RecommenderAgent."""

    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = RecommenderAgent()
        assert agent.name == "RecommenderAgent"
        assert "build_recommendation" in agent.capabilities

    async def test_input_validation_success(self):
        """Test input validation passes with valid data."""
        agent = RecommenderAgent()
        inputs = {
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW"
        }
        await agent.validate_inputs(inputs)

    async def test_input_validation_missing_field(self):
        """Test input validation fails with missing field."""
        agent = RecommenderAgent()
        inputs = {"profession": "Guardian"}
        
        with pytest.raises(ValueError, match="Missing required fields"):
            await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_profession(self):
        """Test input validation fails with invalid profession."""
        agent = RecommenderAgent()
        inputs = {
            "profession": "InvalidClass",
            "role": "Support",
            "game_mode": "WvW"
        }
        
        with pytest.raises(ValueError, match="Invalid profession"):
            await agent.validate_inputs(inputs)

    async def test_prompt_building(self):
        """Test prompt is correctly built."""
        agent = RecommenderAgent()
        prompt = agent._build_prompt("Guardian", "Support", "WvW", "")
        
        assert "Guardian" in prompt
        assert "Support" in prompt
        assert "WvW" in prompt
        assert "Guild Wars 2" in prompt


class TestSynergyAgent:
    """Tests for SynergyAgent."""

    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = SynergyAgent()
        assert agent.name == "SynergyAgent"
        assert "team_composition_analysis" in agent.capabilities

    async def test_input_validation_success(self):
        """Test input validation passes with valid data."""
        agent = SynergyAgent()
        inputs = {
            "professions": ["Guardian", "Warrior", "Mesmer"],
            "game_mode": "WvW"
        }
        await agent.validate_inputs(inputs)

    async def test_input_validation_too_few_professions(self):
        """Test input validation fails with too few professions."""
        agent = SynergyAgent()
        inputs = {"professions": ["Guardian"]}
        
        with pytest.raises(ValueError, match="at least 2 professions"):
            await agent.validate_inputs(inputs)

    async def test_compare_compositions(self):
        """Test composition comparison."""
        agent = SynergyAgent()
        comp_a = ["Guardian", "Warrior"]
        comp_b = ["Guardian", "Mesmer"]
        
        # This would require mocking the AI calls
        # For now, just test the method exists
        assert hasattr(agent, 'compare_compositions')


class TestOptimizerAgent:
    """Tests for OptimizerAgent."""

    async def test_agent_initialization(self):
        """Test agent can be initialized."""
        agent = OptimizerAgent()
        assert agent.name == "OptimizerAgent"
        assert "composition_optimization" in agent.capabilities

    async def test_input_validation_success(self):
        """Test input validation passes with valid data."""
        agent = OptimizerAgent()
        inputs = {
            "current_composition": ["Guardian", "Warrior"],
            "objectives": ["maximize_boons"],
            "game_mode": "Raids"
        }
        await agent.validate_inputs(inputs)

    async def test_input_validation_invalid_objective(self):
        """Test input validation fails with invalid objective."""
        agent = OptimizerAgent()
        inputs = {
            "current_composition": ["Guardian", "Warrior"],
            "objectives": ["invalid_objective"]
        }
        
        with pytest.raises(ValueError, match="Invalid objective"):
            await agent.validate_inputs(inputs)
```

---

### 6. Créer Documentation Base (2 heures)

#### Fichier: `.env.example`

```bash
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite+aiosqlite:///./gw2optimizer.db

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Ollama / Mistral
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# Redis
REDIS_ENABLED=True
REDIS_URL=redis://localhost:6379/0

# Learning System
LEARNING_ENABLED=True
LEARNING_DATA_DIR=./data/learning
MAX_LEARNING_ITEMS=10000

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/gw2optimizer.log
```

#### Fichier: `INSTALLATION.md`

````markdown
# 📦 Installation GW2Optimizer

## Prérequis

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (ou SQLite)
- Ollama avec Mistral 7B
- Redis (optionnel)

## Backend

### 1. Cloner le repository
```bash
git clone https://github.com/votre-repo/GW2Optimizer.git
cd GW2Optimizer/backend
```

### 2. Créer environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer variables d'environnement
```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

### 5. Initialiser base de données
```bash
alembic upgrade head
```

### 6. Démarrer Ollama
```bash
ollama pull mistral
ollama serve
```

### 7. Lancer le serveur
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

### 1. Installer dépendances
```bash
cd frontend
npm install
```

### 2. Configurer environnement
```bash
cp .env.example .env
# Éditer .env
```

### 3. Lancer le serveur de développement
```bash
npm run dev
```

## Tests

```bash
cd backend
pytest -v --cov=app
```

## Accès

- **Backend API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
````

---

## 🟢 PRIORITÉ FAIBLE - CE MOIS

### 7. Optimisations Performance
### 8. Monitoring et Métriques
### 9. Documentation Complète
### 10. Tests E2E

---

## ✅ CHECKLIST CORRECTIONS

### Court Terme (1-3 jours)
- [ ] Corriger fixtures tests (test_user)
- [ ] Mettre à jour test_auth.py
- [ ] Supprimer fichiers dupliqués
- [ ] Créer endpoints workflows IA
- [ ] Créer tests agents basiques
- [ ] Créer structure frontend
- [ ] Déplacer composants frontend
- [ ] Créer package.json
- [ ] Créer .env.example
- [ ] Créer INSTALLATION.md

### Moyen Terme (1-2 semaines)
- [ ] Tests workflows complets
- [ ] Tests intégration IA
- [ ] Créer Chatbox
- [ ] Créer BuildVisualization
- [ ] Thème GW2
- [ ] Icônes GW2
- [ ] Documentation API complète

### Long Terme (1 mois)
- [ ] Tests E2E
- [ ] Monitoring
- [ ] PWA
- [ ] i18n
- [ ] Wiki

---

**Dernière mise à jour**: 20 Octobre 2025, 16:15 UTC+02:00
