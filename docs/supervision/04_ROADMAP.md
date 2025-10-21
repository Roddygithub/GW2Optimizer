# 04 - Roadmap & Recommandations

**Section**: Feuille de Route Technique  
**Version**: v6.0 → v7.0  
**Date**: 2025-10-21

---

## 🗺️ VISION GLOBALE

### Objectif GW2Optimizer

**Mission**: Logiciel d'optimisation d'escouades pour Guild Wars 2 (McM/WvW)

**Valeur ajoutée**:
- 🎯 Recommandations builds optimisées (IA)
- 👥 Compositions d'équipe synergiques
- 📊 Analytics temps réel (WebSocket)
- 🤖 Agents multi-IA pour optimisation
- 📚 Intégration données officielles GW2

---

## 🎯 ROADMAP PAR PRIORITÉ

### 🔴 PRIORITÉ HAUTE (1-2 semaines)

#### 1. Fixtures Tests Services ⏱️ 1h

**Statut**: En attente  
**Bloquant**: 15 tests services

**Action**:
```python
# tests/conftest.py
@pytest.fixture
def sample_build_data():
    return {
        "name": "Test Guardian Build",
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
        "is_public": True,
    }
```

**Impact**: 15 tests débloqués, +3% coverage

#### 2. Migration Alembic PostgreSQL ⏱️ 2h

**Statut**: À faire  
**Nécessaire**: Production

**Actions**:
```bash
cd backend

# Créer migration initiale
alembic revision --autogenerate -m "Initial schema with GUID type"

# Vérifier migration générée
cat alembic/versions/*_initial_schema.py

# Appliquer en dev
alembic upgrade head

# Tester avec PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost/gw2opt alembic upgrade head
```

**Validation**:
```sql
-- Vérifier tables créées
\dt

-- Vérifier type UUID
\d users
-- id devrait être UUID PRIMARY KEY
```

#### 3. Tests Auth Service ⏱️ 4h

**Statut**: À créer  
**Coverage**: 0% → 80%

**Fichier**: `tests/test_services/test_auth_service.py`

**Tests à créer**:
```python
def test_verify_password()
def test_get_password_hash()
def test_authenticate_user_success()
def test_authenticate_user_wrong_password()
def test_create_user()
def test_get_user_by_email()
def test_get_user_by_username()
def test_update_user()
def test_failed_login_attempts()
def test_account_locking()
```

**Impact**: +10% coverage global

---

### 🟡 PRIORITÉ MOYENNE (2-4 semaines)

#### 4. Frontend Moderne ⏱️ 2 semaines

**Statut**: Ancien design à remplacer  
**Objectif**: Interface moderne GW2-themed

**Stack Recommandé**:
```typescript
// Frontend v2.0
- Framework: React 18 + TypeScript
- UI: TailwindCSS + HeadlessUI
- State: Zustand
- Data Fetching: React Query + Axios
- Routing: React Router v6
- Forms: React Hook Form + Zod
- Icons: Lucide React
- Build: Vite
```

**Palette Couleurs GW2**:
```css
/* Theme GW2 Officiel */
:root {
  /* Primary colors */
  --gw2-gold: #C8AA6E;
  --gw2-blue: #2C5AA0;
  --gw2-red: #B91919;
  
  /* Neutral colors */
  --gw2-dark: #1A1A1A;
  --gw2-gray: #3D3D3D;
  --gw2-light: #F5F5DC;
  
  /* Profession colors */
  --guardian: #72C1D9;
  --warrior: #FFD166;
  --engineer: #D09C59;
  --ranger: #8CDC82;
  --thief: #C08F95;
  --elementalist: #F68A87;
  --mesmer: #B679D5;
  --necromancer: #52A76F;
  --revenant: #D16E5A;
}
```

**Composants Prioritaires**:

1. **BuildCard** - Affichage build compact
   ```tsx
   interface BuildCardProps {
     build: Build;
     onClick?: () => void;
     showAuthor?: boolean;
   }
   ```

2. **TeamComposer** - Drag & drop builds
   ```tsx
   interface TeamComposerProps {
     team: Team;
     availableBuilds: Build[];
     onUpdate: (team: Team) => void;
   }
   ```

3. **ProfessionSelector** - Icônes officielles
   ```tsx
   interface ProfessionSelectorProps {
     selected?: Profession;
     onChange: (profession: Profession) => void;
     mode: 'grid' | 'list';
   }
   ```

4. **SynergyVisualizer** - Graph interactif
   ```tsx
   interface SynergyVisualizerProps {
     builds: Build[];
     highlightSynergies?: boolean;
   }
   ```

5. **McMDashboard** - Analytics temps réel
   ```tsx
   interface McMDashboardProps {
     wsUrl: string;
     refreshInterval?: number;
   }
   ```

**Structure Frontend**:
```
frontend/
├── src/
│   ├── components/
│   │   ├── builds/
│   │   │   ├── BuildCard.tsx
│   │   │   ├── BuildForm.tsx
│   │   │   └── BuildList.tsx
│   │   ├── teams/
│   │   │   ├── TeamComposer.tsx
│   │   │   ├── TeamCard.tsx
│   │   │   └── TeamList.tsx
│   │   ├── professions/
│   │   │   ├── ProfessionIcon.tsx
│   │   │   └── ProfessionSelector.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       └── Input.tsx
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── BuildsPage.tsx
│   │   ├── TeamsPage.tsx
│   │   └── McMDashboard.tsx
│   ├── hooks/
│   │   ├── useBuilds.ts
│   │   ├── useTeams.ts
│   │   └── useWebSocket.ts
│   ├── api/
│   │   ├── client.ts
│   │   ├── builds.ts
│   │   └── teams.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── buildsStore.ts
│   │   └── teamsStore.ts
│   └── types/
│       ├── build.ts
│       ├── team.ts
│       └── user.ts
├── public/
│   └── icons/
│       └── professions/
│           ├── guardian.svg
│           ├── warrior.svg
│           └── ...
└── package.json
```

#### 5. Intégration GW2 API Officielle ⏱️ 1 semaine

**Statut**: Client partiel  
**Objectif**: Données officielles temps réel

**Endpoints à intégrer**:

```python
# backend/app/services/gw2_api_client.py

class GW2APIClient:
    BASE_URL = "https://api.guildwars2.com"
    
    async def get_professions(self) -> List[Profession]:
        """Get all professions."""
        return await self._get("/v2/professions")
    
    async def get_specializations(self, profession: str) -> List[Specialization]:
        """Get specializations for profession."""
        return await self._get(f"/v2/professions/{profession}/specializations")
    
    async def get_skills(self, profession: str) -> List[Skill]:
        """Get skills for profession."""
        return await self._get(f"/v2/professions/{profession}/skills")
    
    async def get_traits(self, specialization_id: int) -> List[Trait]:
        """Get traits for specialization."""
        return await self._get(f"/v2/traits?ids={specialization_id}")
    
    async def get_equipment_stats(self) -> List[EquipmentStat]:
        """Get equipment stat combinations."""
        return await self._get("/v2/itemstats")
```

**Caching Redis**:
```python
@cacheable(ttl=3600)  # 1 heure
async def get_professions(self) -> List[Profession]:
    ...
```

#### 6. Coverage 60% ⏱️ 2 semaines

**État actuel**: 30.63%  
**Objectif**: 60%

**Plan d'action**: Voir [Tests & Coverage](./03_TESTS_COVERAGE.md)

---

### 🟢 PRIORITÉ BASSE (1-2 mois)

#### 7. Agents IA Avancés ⏱️ 3 semaines

**Statut**: RecommenderAgent existe  
**Objectif**: Suite complète agents

**Architecture Agents**:

```python
# backend/app/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, model: str = "llama2"):
        self.model = model
        self.ollama = OllamaClient()
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic."""
        pass
```

**Agents à Créer**:

1. **OptimizerAgent** - Optimisation statistique
   ```python
   class OptimizerAgent(BaseAgent):
       async def execute(self, context):
           """Optimize build stats (DPS, HPS, Toughness)."""
           build = context["build"]
           constraints = context.get("constraints", {})
           
           # Calculate optimal gear/traits
           optimized = await self._optimize(build, constraints)
           return {"optimized_build": optimized}
   ```

2. **SynergyAgent** - Détection synergies
   ```python
   class SynergyAgent(BaseAgent):
       async def execute(self, context):
           """Detect synergies between builds."""
           builds = context["builds"]
           
           # Analyze boons, conditions, combos
           synergies = await self._analyze_synergies(builds)
           return {"synergies": synergies}
   ```

3. **MetaAnalysisAgent** - Analyse méta
   ```python
   class MetaAnalysisAgent(BaseAgent):
       async def execute(self, context):
           """Analyze current meta trends."""
           game_mode = context["game_mode"]
           
           # Scrape meta builds, analyze popularity
           meta = await self._analyze_meta(game_mode)
           return {"meta_analysis": meta}
   ```

4. **CounterAgent** - Détection counters
   ```python
   class CounterAgent(BaseAgent):
       async def execute(self, context):
           """Suggest counter builds."""
           enemy_builds = context["enemy_builds"]
           
           # Find effective counters
           counters = await self._find_counters(enemy_builds)
           return {"counter_builds": counters}
   ```

**Workflow Multi-Agents**:

```python
# backend/app/workflows/squad_optimization_workflow.py

class SquadOptimizationWorkflow:
    def __init__(self):
        self.recommender = RecommenderAgent()
        self.optimizer = OptimizerAgent()
        self.synergy = SynergyAgent()
    
    async def execute(self, requirements: SquadRequirements) -> Squad:
        """Optimize full squad composition."""
        
        # 1. Recommend builds for each role
        builds = await self.recommender.execute({
            "roles": requirements.roles,
            "game_mode": requirements.game_mode
        })
        
        # 2. Optimize each build
        optimized = []
        for build in builds["recommended_builds"]:
            result = await self.optimizer.execute({"build": build})
            optimized.append(result["optimized_build"])
        
        # 3. Analyze team synergies
        synergies = await self.synergy.execute({"builds": optimized})
        
        return Squad(
            builds=optimized,
            synergies=synergies["synergies"],
            score=self._calculate_score(optimized, synergies)
        )
```

#### 8. Wiki Scraper & Ingestion ⏱️ 2 semaines

**Statut**: À créer  
**Objectif**: Données communautaires

**Sources**:
- https://wiki.guildwars2.com/
- https://snowcrows.com/ (PvE)
- https://gw2mists.com/ (WvW)
- https://metabattle.com/ (PvP/WvW)

**Scraper Architecture**:

```python
# backend/app/services/scraper/wiki_scraper.py

class WikiScraper:
    async def scrape_profession_page(self, profession: str) -> ProfessionData:
        """Scrape profession wiki page."""
        url = f"https://wiki.guildwars2.com/wiki/{profession}"
        html = await self._fetch(url)
        
        return {
            "name": profession,
            "description": self._extract_description(html),
            "mechanics": self._extract_mechanics(html),
            "trait_lines": self._extract_trait_lines(html),
        }
    
    async def scrape_meta_builds(self, source: str, game_mode: str) -> List[Build]:
        """Scrape meta builds from community sites."""
        if source == "snowcrows":
            return await self._scrape_snowcrows(game_mode)
        elif source == "metabattle":
            return await self._scrape_metabattle(game_mode)
```

**Ingestion Pipeline**:

```python
# backend/app/workflows/data_ingestion_workflow.py

class DataIngestionWorkflow:
    async def ingest_all(self):
        """Ingest all external data sources."""
        
        # 1. GW2 Official API
        await self._ingest_official_api()
        
        # 2. Wiki data
        await self._ingest_wiki()
        
        # 3. Meta builds
        await self._ingest_meta_builds()
        
        # 4. Update embeddings for AI
        await self._update_embeddings()
```

#### 9. Production Deployment ⏱️ 1 semaine

**Infrastructure**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/gw2opt
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=secret
  
  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
  
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  pgdata:
  redisdata:
```

**Kubernetes** (optionnel):

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gw2optimizer-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gw2optimizer-backend
  template:
    metadata:
      labels:
        app: gw2optimizer-backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/roddygithub/gw2optimizer:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: gw2opt-secrets
              key: database-url
```

---

## 📋 PRODUCTION CHECKLIST

### Sécurité

- [ ] **JWT Secret**: Variables d'environnement sécurisées
- [ ] **HTTPS**: SSL/TLS configuré
- [ ] **CORS**: Whitelist domaines autorisés
- [ ] **Rate Limiting**: Protection DDoS
- [ ] **SQL Injection**: ORM paramétrisé (déjà OK)
- [ ] **XSS Protection**: FastAPI (déjà OK)
- [ ] **CSRF Tokens**: Pour formulaires
- [ ] **Secrets Manager**: AWS Secrets / HashiCorp Vault

### Base de Données

- [ ] **PostgreSQL 15+**: Version production
- [ ] **Migrations**: Alembic configuré
- [ ] **Backups**: Automatisés quotidiens
- [ ] **Replication**: Master-slave
- [ ] **Monitoring**: pg_stat_statements
- [ ] **Connection Pooling**: pgBouncer
- [ ] **Indexes**: Optimisés (user_id, profession, game_mode)

### Performance

- [ ] **Redis Cache**: Actif + circuit breaker
- [ ] **CDN**: Cloudflare/AWS CloudFront
- [ ] **Compression**: gzip/brotli
- [ ] **Query Optimization**: EXPLAIN ANALYZE
- [ ] **Async Endpoints**: FastAPI async (déjà OK)
- [ ] **Load Balancing**: Nginx/HAProxy

### Monitoring

- [ ] **Logs**: JSON structuré (Elastic/Loki)
- [ ] **Metrics**: Prometheus + Grafana
- [ ] **Tracing**: Jaeger/OpenTelemetry
- [ ] **Alerts**: PagerDuty/Slack
- [ ] **Health Checks**: `/health` endpoint
- [ ] **Error Tracking**: Sentry

### CI/CD

- [ ] **Tests Auto**: pytest sur chaque push
- [ ] **Coverage**: >60% requis
- [ ] **Docker Build**: Automatisé
- [ ] **Security Scan**: Trivy/Snyk
- [ ] **Deploy**: GitHub Actions → Kubernetes

---

## 🎯 MILESTONES

### v6.1 (2 semaines)

- ✅ UUID/SQLite fix
- ⏳ Fixtures tests (15 tests débloqués)
- ⏳ Migration Alembic
- ⏳ Tests auth_service
- **Coverage**: 30% → 45%

### v6.5 (1 mois)

- ⏳ Frontend moderne (React + TypeScript)
- ⏳ GW2 API integration complète
- ⏳ Coverage 60%
- **Features**: UI moderne, données officielles

### v7.0 (2 mois)

- ⏳ Agents IA avancés (4 agents)
- ⏳ Wiki scraper & ingestion
- ⏳ Production deployment
- **Features**: Suite IA complète, data pipeline

---

[← Tests](./03_TESTS_COVERAGE.md) | [Index](./00_INDEX.md) | [Guide Reprise →](./05_GUIDE_REPRISE.md)
