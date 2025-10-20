# 🏗️ Architecture - GW2Optimizer

**Version**: v1.2.0  
**Date**: 20 Octobre 2025

---

## 📊 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────┐
│                    GW2Optimizer                         │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Frontend   │ ◄─────► │   Backend    │            │
│  │ React + Vite │  HTTP   │   FastAPI    │            │
│  └──────────────┘         └──────┬───────┘            │
│                                   │                     │
│                          ┌────────┴────────┐           │
│                          │                 │           │
│                    ┌─────▼─────┐    ┌─────▼─────┐    │
│                    │  Database │    │    Redis  │    │
│                    │PostgreSQL │    │   Cache   │    │
│                    └───────────┘    └───────────┘    │
│                                                         │
│                          ┌──────────────┐             │
│                          │    Ollama    │             │
│                          │  Mistral 7B  │             │
│                          └──────────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Architecture Backend

### Structure des Dossiers

```
backend/
├── app/
│   ├── agents/              # Agents IA Mistral
│   │   ├── base.py          # BaseAgent
│   │   ├── recommender_agent.py
│   │   ├── synergy_agent.py
│   │   └── optimizer_agent.py
│   │
│   ├── workflows/           # Workflows d'orchestration
│   │   ├── base.py          # BaseWorkflow
│   │   ├── build_optimization_workflow.py
│   │   ├── team_analysis_workflow.py
│   │   └── learning_workflow.py
│   │
│   ├── api/                 # Endpoints API
│   │   ├── auth.py          # Authentification
│   │   ├── ai.py            # Endpoints IA
│   │   ├── builds.py        # Builds
│   │   ├── teams.py         # Équipes
│   │   └── chat.py          # Chat
│   │
│   ├── core/                # Configuration centrale
│   │   ├── config.py        # Settings
│   │   ├── security.py      # JWT, OAuth2
│   │   ├── cache.py         # Cache Redis
│   │   ├── redis.py         # Client Redis
│   │   └── circuit_breaker.py
│   │
│   ├── db/                  # Base de données
│   │   ├── base.py          # SQLAlchemy Base
│   │   ├── session.py       # Session async
│   │   └── init_db.py       # Initialisation
│   │
│   ├── models/              # Modèles de données
│   │   ├── user.py          # User + LoginHistory
│   │   ├── build.py         # Build
│   │   ├── team.py          # Team
│   │   └── token.py         # Token schemas
│   │
│   ├── services/            # Logique métier
│   │   ├── ai_service.py    # Service IA centralisé
│   │   ├── auth_service.py  # Authentification
│   │   ├── user_service.py  # Gestion users
│   │   ├── build_service_db.py
│   │   ├── team_service_db.py
│   │   ├── parser/          # Parser GW2Skill
│   │   ├── learning/        # Système learning
│   │   ├── scraper/         # Web scraping
│   │   └── exporter/        # Export formats
│   │
│   ├── learning/            # Apprentissage continu
│   │   ├── data/
│   │   │   ├── collector.py # Collecte données
│   │   │   └── storage.py   # Stockage
│   │   └── models/          # Modèles ML
│   │
│   ├── middleware.py        # Middleware sécurité
│   ├── exceptions.py        # Gestion erreurs
│   └── main.py              # Application principale
│
├── alembic/                 # Migrations DB
├── tests/                   # Tests
├── logs/                    # Logs application
└── data/                    # Données learning
```

### Flux de Données

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ HTTP Request
     ▼
┌────────────────┐
│   Middleware   │ ◄── Security Headers, CORS, Logging
└────┬───────────┘
     │
     ▼
┌────────────────┐
│   API Router   │ ◄── /api/v1/auth, /api/v1/ai, etc.
└────┬───────────┘
     │
     ▼
┌────────────────┐
│   Service      │ ◄── Business Logic
└────┬───────────┘
     │
     ├──────────────┐
     │              │
     ▼              ▼
┌─────────┐   ┌──────────┐
│Database │   │  Cache   │
│(SQLAlch)│   │ (Redis)  │
└─────────┘   └──────────┘
     │
     ▼
┌────────────────┐
│   Response     │
└────────────────┘
```

---

## 🤖 Architecture IA

### Agents IA

```
┌─────────────────────────────────────────┐
│           AIService (Central)           │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │      Agent Registry             │  │
│  │  - RecommenderAgent             │  │
│  │  - SynergyAgent                 │  │
│  │  - OptimizerAgent               │  │
│  └─────────────────────────────────┘  │
│                                         │
│  ┌─────────────────────────────────┐  │
│  │     Workflow Registry           │  │
│  │  - BuildOptimizationWorkflow    │  │
│  │  - TeamAnalysisWorkflow         │  │
│  │  - LearningWorkflow             │  │
│  └─────────────────────────────────┘  │
└─────────────┬───────────────────────────┘
              │
              ▼
      ┌───────────────┐
      │    Ollama     │
      │  Mistral 7B   │
      └───────────────┘
```

### Workflow d'Exécution

```
1. Client Request
   │
   ▼
2. API Endpoint (/api/v1/ai/recommend-build)
   │
   ▼
3. AIService.run_agent("recommender", inputs)
   │
   ├─► 4. Validate Inputs
   │
   ├─► 5. Execute Agent
   │   │
   │   ├─► Build Prompt
   │   │
   │   ├─► Call Ollama API
   │   │
   │   └─► Parse Response
   │
   └─► 6. Return Result
```

### Système d'Apprentissage

```
┌──────────────────────────────────────────┐
│        Learning Pipeline                 │
│                                          │
│  1. Data Collection                      │
│     ├─► User interactions                │
│     ├─► Build ratings                    │
│     └─► Team compositions                │
│                                          │
│  2. Data Storage                         │
│     ├─► JSON compressed                  │
│     ├─► Anonymization                    │
│     └─► Cleanup old data                 │
│                                          │
│  3. Evaluation                           │
│     ├─► Quality metrics                  │
│     ├─► Performance analysis             │
│     └─► Selection criteria               │
│                                          │
│  4. Fine-tuning (Future)                 │
│     ├─► Model adaptation                 │
│     ├─► Prompt optimization              │
│     └─► Continuous improvement           │
│                                          │
│  5. Scheduler (APScheduler)              │
│     ├─► Collect: Every 1h                │
│     ├─► Evaluate: Every 24h              │
│     └─► Cleanup: Every 7d                │
└──────────────────────────────────────────┘
```

---

## 🎨 Architecture Frontend

### Structure des Dossiers

```
frontend/
├── src/
│   ├── components/
│   │   ├── Auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── Build/
│   │   │   ├── BuildCard.tsx
│   │   │   └── BuildVisualization.tsx
│   │   ├── Team/
│   │   │   ├── TeamCard.tsx
│   │   │   └── TeamComposition.tsx
│   │   ├── Chat/
│   │   │   └── Chatbox.tsx
│   │   ├── AI/
│   │   │   ├── AIRecommender.tsx
│   │   │   └── AIStatus.tsx
│   │   └── Common/
│   │       ├── Header.tsx
│   │       ├── Footer.tsx
│   │       └── Loading.tsx
│   │
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── ProfilePage.tsx
│   │   └── SettingsPage.tsx
│   │
│   ├── services/
│   │   ├── api.ts           # API client
│   │   └── auth.ts          # Auth service
│   │
│   ├── contexts/
│   │   └── AuthContext.tsx  # Auth context
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useAI.ts
│   │
│   ├── utils/
│   │   └── helpers.ts
│   │
│   ├── styles/
│   │   └── globals.css
│   │
│   └── App.tsx
│
├── public/
│   └── icons/
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### Flux de Données React

```
┌──────────────┐
│  Component   │
└──────┬───────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌──────────┐   ┌──────────┐
│  Context │   │   Hook   │
└────┬─────┘   └────┬─────┘
     │              │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │ API Service  │
     └──────┬───────┘
            │ HTTP
            ▼
     ┌──────────────┐
     │   Backend    │
     └──────────────┘
```

---

## 🔐 Architecture Sécurité

### Authentification JWT

```
┌──────────────────────────────────────────┐
│         JWT Authentication               │
│                                          │
│  1. Login                                │
│     ├─► Validate credentials            │
│     ├─► Generate access token (30min)   │
│     ├─► Generate refresh token (7d)     │
│     └─► Store in Redis + Cookie         │
│                                          │
│  2. Request with Token                   │
│     ├─► Extract from header/cookie      │
│     ├─► Verify signature                │
│     ├─► Check expiration                │
│     ├─► Check revocation (Redis)        │
│     └─► Get user from DB                │
│                                          │
│  3. Token Refresh                        │
│     ├─► Validate refresh token          │
│     ├─► Generate new access token       │
│     └─► Return new tokens                │
│                                          │
│  4. Logout                               │
│     ├─► Add token to revocation list    │
│     ├─► Clear cookie                    │
│     └─► Expire in Redis                 │
└──────────────────────────────────────────┘
```

### Middleware de Sécurité

```
Request
  │
  ▼
┌─────────────────────┐
│ CORS Middleware     │ ◄── Origins, Methods, Headers
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Security Headers    │ ◄── CSP, HSTS, X-Frame-Options
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Rate Limiting       │ ◄── SlowAPI (60/min, 1000/h)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Authentication      │ ◄── JWT Validation
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Authorization       │ ◄── Role/Permission Check
└──────────┬──────────┘
           │
           ▼
      API Handler
```

---

## 💾 Architecture Base de Données

### Schéma de Données

```sql
┌─────────────────┐
│     users       │
├─────────────────┤
│ id (PK)         │
│ email           │
│ username        │
│ hashed_password │
│ is_active       │
│ is_verified     │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────▼─────────────┐
    │  login_history   │
    ├──────────────────┤
    │ id (PK)          │
    │ user_id (FK)     │
    │ ip_address       │
    │ user_agent       │
    │ success          │
    │ timestamp        │
    └──────────────────┘

┌─────────────────┐
│     builds      │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ name            │
│ profession      │
│ role            │
│ game_mode       │
│ traits          │
│ skills          │
│ equipment       │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│     teams       │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ name            │
│ game_mode       │
│ composition     │
│ synergy_score   │
│ created_at      │
└─────────────────┘
```

### Migrations Alembic

```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   └── 002_add_learning_tables.py
├── env.py
└── script.py.mako
```

---

## 🚀 Déploiement

### Architecture Production

```
┌─────────────────────────────────────────────┐
│              Load Balancer                  │
│              (Nginx/Traefik)                │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  Frontend   │  │  Backend    │
│  (Static)   │  │  (Uvicorn)  │
│  Nginx      │  │  Gunicorn   │
└─────────────┘  └──────┬──────┘
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
       ┌────────────┐      ┌────────────┐
       │ PostgreSQL │      │   Redis    │
       │  (Primary) │      │  (Cache)   │
       └────────────┘      └────────────┘
              │
              ▼
       ┌────────────┐
       │ PostgreSQL │
       │ (Replica)  │
       └────────────┘
```

### Scalabilité

```
Horizontal Scaling:
- Multiple backend instances
- Load balancer distribution
- Shared Redis cache
- Database replication

Vertical Scaling:
- Increase CPU/RAM
- Optimize queries
- Cache optimization
- Connection pooling
```

---

## 📊 Monitoring

### Métriques Collectées

```
Application:
- Request count
- Response time
- Error rate
- Active users

IA:
- Agent execution time
- Workflow completion rate
- Ollama response time
- Cache hit rate

Database:
- Query performance
- Connection pool
- Transaction rate
- Slow queries

System:
- CPU usage
- Memory usage
- Disk I/O
- Network traffic
```

### Stack Monitoring (Futur)

```
┌──────────────┐
│ Application  │
└──────┬───────┘
       │ Metrics
       ▼
┌──────────────┐
│ Prometheus   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Grafana    │ ◄── Dashboards
└──────────────┘

┌──────────────┐
│    Sentry    │ ◄── Error Tracking
└──────────────┘
```

---

## 🔄 CI/CD Pipeline (Futur)

```
┌──────────────┐
│  Git Push    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ GitHub       │
│ Actions      │
└──────┬───────┘
       │
       ├─► Lint (flake8, eslint)
       ├─► Tests (pytest, vitest)
       ├─► Build (Docker)
       ├─► Security Scan
       └─► Deploy (Staging/Prod)
```

---

## 📚 Technologies Utilisées

### Backend
- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Cache**: Redis + aioredis
- **IA**: Ollama + Mistral 7B
- **Auth**: JWT + OAuth2
- **Validation**: Pydantic v2
- **Tests**: pytest + pytest-asyncio

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Language**: TypeScript 5
- **Styling**: TailwindCSS 3
- **Icons**: Lucide React
- **State**: React Query
- **Tests**: Vitest

### Infrastructure
- **Database**: PostgreSQL 14+ / SQLite
- **Cache**: Redis 6+
- **Web Server**: Nginx / Uvicorn
- **Container**: Docker (optionnel)
- **Orchestration**: Docker Compose

---

## 🎯 Principes Architecturaux

### 1. Séparation des Préoccupations
- API ↔ Services ↔ Models ↔ Database
- Frontend ↔ Backend via REST API

### 2. Async/Await Partout
- SQLAlchemy async
- httpx async pour Ollama
- FastAPI async handlers

### 3. Modularité
- Agents IA indépendants
- Workflows composables
- Services découplés

### 4. Résilience
- Circuit breaker pour Redis
- Fallback cache disque
- Graceful degradation

### 5. Sécurité
- JWT avec révocation
- Rate limiting
- Input validation
- Security headers

### 6. Observabilité
- Logging structuré
- Correlation IDs
- Error tracking
- Performance metrics

---

## 📖 Références

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [React Architecture](https://react.dev/learn/thinking-in-react)
- [Twelve-Factor App](https://12factor.net/)

---

**Document maintenu par**: Équipe GW2Optimizer  
**Dernière mise à jour**: 20 Octobre 2025
