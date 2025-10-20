# 🔧 RÉORGANISATION COMPLÈTE - GW2Optimizer

**Date**: 20 Octobre 2025, 16:34  
**Objectif**: Atteindre 100% de complétude  
**Score Actuel**: 94/100

---

## 🎯 ACTIONS PRIORITAIRES (Ordre d'exécution)

### 🔴 PHASE 1: Nettoyage Backend (15 min)

#### 1.1 Supprimer fichiers dupliqués
```bash
cd /home/roddy/GW2Optimizer/backend

# Supprimer anciens services IA
rm app/ai_service.py
rm app/core/ai_service.py

# Vérifier qu'aucun import ne pointe vers ces fichiers
grep -r "from app.ai_service import" . --exclude-dir=__pycache__
grep -r "from app.core.ai_service import" . --exclude-dir=__pycache__
```

#### 1.2 Créer endpoints workflows IA
**Fichier**: `backend/app/api/ai.py`

Ajouter à la fin du fichier:
```python
@router.post(
    "/optimize-team",
    response_model=Dict[str, Any],
    summary="Optimize Team Composition",
    description="Optimize a team composition using the OptimizerAgent",
    dependencies=[Depends(get_current_active_user)],
)
async def optimize_team(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Optimize a team composition.
    
    Request body:
    - current_composition: List[str] - Current team professions
    - objectives: List[str] - Optimization objectives
    - game_mode: str - Game mode (PvE, PvP, WvW, etc.)
    - max_changes: int - Maximum number of changes allowed
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.run_agent("optimizer", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error optimizing team: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )


@router.post(
    "/workflow/build-optimization",
    response_model=Dict[str, Any],
    summary="Execute Build Optimization Workflow",
    description="Execute the complete build optimization workflow",
    dependencies=[Depends(get_current_active_user)],
)
async def execute_build_optimization(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Execute the complete build optimization workflow.
    
    Request body:
    - profession: str - Character profession
    - role: str - Desired role
    - game_mode: str - Game mode
    - team_composition: List[str] - Optional team composition
    - optimization_iterations: int - Number of optimization iterations
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.execute_workflow("build_optimization", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error executing build optimization workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Workflow execution error: {str(e)}"
        )


@router.post(
    "/workflow/team-analysis",
    response_model=Dict[str, Any],
    summary="Execute Team Analysis Workflow",
    description="Execute the complete team analysis workflow",
    dependencies=[Depends(get_current_active_user)],
)
async def execute_team_analysis(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Execute the complete team analysis workflow.
    
    Request body:
    - professions: List[str] - Team professions
    - game_mode: str - Game mode
    - optimize: bool - Whether to optimize the composition
    - max_changes: int - Maximum changes for optimization
    """
    try:
        ai_service = AIService()
        await ai_service.initialize()
        result = await ai_service.execute_workflow("team_analysis", request)
        await ai_service.cleanup()
        return result
    except Exception as e:
        logger.error(f"Error executing team analysis workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Workflow execution error: {str(e)}"
        )
```

---

### 🔴 PHASE 2: Tests IA (1h)

#### 2.1 Créer tests agents
**Fichier**: `backend/tests/test_agents.py`

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

#### 2.2 Créer tests workflows
**Fichier**: `backend/tests/test_workflows.py`

```python
"""Tests for AI Workflows."""
import pytest
from app.workflows.build_optimization_workflow import BuildOptimizationWorkflow
from app.workflows.team_analysis_workflow import TeamAnalysisWorkflow

pytestmark = pytest.mark.asyncio


class TestBuildOptimizationWorkflow:
    """Tests for BuildOptimizationWorkflow."""

    async def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = BuildOptimizationWorkflow()
        assert workflow.name == "BuildOptimizationWorkflow"
        assert len(workflow.steps) > 0

    async def test_workflow_input_validation(self):
        """Test workflow input validation."""
        workflow = BuildOptimizationWorkflow()
        inputs = {
            "profession": "Guardian",
            "role": "Support",
            "game_mode": "WvW"
        }
        await workflow.validate_inputs(inputs)


class TestTeamAnalysisWorkflow:
    """Tests for TeamAnalysisWorkflow."""

    async def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = TeamAnalysisWorkflow()
        assert workflow.name == "TeamAnalysisWorkflow"
        assert len(workflow.steps) > 0

    async def test_workflow_input_validation(self):
        """Test workflow input validation."""
        workflow = TeamAnalysisWorkflow()
        inputs = {
            "professions": ["Guardian", "Warrior", "Mesmer"],
            "game_mode": "WvW"
        }
        await workflow.validate_inputs(inputs)
```

---

### 🟡 PHASE 3: Réorganisation Frontend (2h)

#### 3.1 Créer structure frontend
```bash
cd /home/roddy/GW2Optimizer

# Créer structure complète
mkdir -p frontend/src/{components,pages,services,hooks,utils,styles,contexts}
mkdir -p frontend/src/components/{Auth,Build,Team,Chat,Common,AI}
mkdir -p frontend/public/icons

# Créer fichiers de configuration
touch frontend/package.json
touch frontend/tsconfig.json
touch frontend/vite.config.ts
touch frontend/tailwind.config.js
touch frontend/.env.example
touch frontend/index.html
```

#### 3.2 Déplacer composants existants
```bash
# Déplacer depuis backend vers frontend
mv backend/app/core/LoginPage.tsx frontend/src/pages/ 2>/dev/null || true
mv backend/app/core/RegisterPage.tsx frontend/src/pages/ 2>/dev/null || true
mv backend/app/DashboardPage.tsx frontend/src/pages/ 2>/dev/null || true
mv backend/app/AIRecommender.tsx frontend/src/components/AI/ 2>/dev/null || true
mv backend/app/TeamAnalyzer.tsx frontend/src/components/Team/ 2>/dev/null || true
mv backend/app/core/api.ts frontend/src/services/ 2>/dev/null || true
mv backend/app/core/App.tsx frontend/src/ 2>/dev/null || true
```

---

### 🟡 PHASE 4: Documentation (1h)

#### 4.1 Créer .env.example
**Fichier**: `backend/.env.example`

```bash
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite+aiosqlite:///./gw2optimizer.db

# Authentication
SECRET_KEY=your-secret-key-change-in-production-min-32-chars
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

---

## ✅ CHECKLIST COMPLÈTE

### Backend
- [ ] Supprimer `app/ai_service.py`
- [ ] Supprimer `app/core/ai_service.py`
- [ ] Ajouter 3 endpoints workflows dans `api/ai.py`
- [ ] Créer `.env.example`

### Tests
- [ ] Créer `tests/test_agents.py`
- [ ] Créer `tests/test_workflows.py`
- [ ] Exécuter `pytest -v`

### Frontend
- [ ] Créer structure `frontend/`
- [ ] Déplacer composants existants
- [ ] Créer `package.json`
- [ ] Créer configs (tsconfig, vite, tailwind)

### Documentation
- [ ] Mettre à jour `README.md`
- [ ] Créer `INSTALLATION.md`
- [ ] Créer `ARCHITECTURE.md`

---

## 🚀 COMMANDES D'EXÉCUTION

```bash
# 1. Nettoyage
cd /home/roddy/GW2Optimizer/backend
rm app/ai_service.py app/core/ai_service.py

# 2. Tests
cd /home/roddy/GW2Optimizer/backend
pytest tests/test_agents.py -v
pytest tests/test_workflows.py -v

# 3. Frontend
cd /home/roddy/GW2Optimizer
mkdir -p frontend/src/{components,pages,services}

# 4. Vérification
cd backend
pytest -v --cov=app
```

---

**Score Cible**: 100/100 après exécution complète
