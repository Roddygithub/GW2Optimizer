# 02 - Architecture Backend

**Section**: Structure et Organisation du Code  
**Version**: v6.0  
**Date**: 2025-10-21

---

## 🏗️ ARCHITECTURE GLOBALE

### Stack Technique

```
┌─────────────────────────────────────┐
│         Frontend (À moderniser)      │
│    React + TypeScript + TailwindCSS  │
└─────────────────┬───────────────────┘
                  │ HTTP/WebSocket
┌─────────────────▼───────────────────┐
│        FastAPI Backend v6.0         │
│  ┌───────────────────────────────┐  │
│  │   API Endpoints (REST + WS)   │  │
│  └───────────────┬───────────────┘  │
│  ┌───────────────▼───────────────┐  │
│  │      Services (Business)      │  │
│  └───────────────┬───────────────┘  │
│  ┌───────────────▼───────────────┐  │
│  │   SQLAlchemy ORM + GUID Type  │  │
│  └───────────────┬───────────────┘  │
└──────────────────┼───────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
┌───▼──────┐              ┌───────▼────┐
│  SQLite  │              │ PostgreSQL │
│  (Tests) │              │   (Prod)   │
└──────────┘              └────────────┘
```

### Technologies

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Backend** | FastAPI | Latest |
| **ORM** | SQLAlchemy | 2.0 (async) |
| **DB Test** | SQLite | 3.x |
| **DB Prod** | PostgreSQL | 12+ |
| **Auth** | JWT + OAuth2 | - |
| **Cache** | Redis | (circuit breaker) |
| **IA** | Ollama | llama2/mistral |
| **Tests** | pytest-asyncio | Latest |
| **Validation** | Pydantic | v2 |

---

## 📂 STRUCTURE PROJET

### Arborescence Backend

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app principale
│   │
│   ├── api/                       # Endpoints REST + WebSocket
│   │   ├── __init__.py
│   │   ├── ai.py                  # Endpoints agents IA
│   │   ├── auth.py                # Authentication/Login
│   │   ├── builds.py              # Builds endpoints (legacy)
│   │   ├── builds_db.py           # Builds DB persistence
│   │   ├── chat.py                # Chat IA
│   │   ├── export.py              # Export builds
│   │   ├── health.py              # Health checks
│   │   ├── learning.py            # Learning endpoints
│   │   ├── meta.py                # Meta analysis
│   │   ├── scraper.py             # Web scraping
│   │   ├── teams.py               # Teams (legacy)
│   │   ├── teams_db.py            # Teams DB persistence
│   │   └── websocket_mcm.py       # WebSocket McM Analytics
│   │
│   ├── services/                  # Business Logic
│   │   ├── __init__.py
│   │   ├── ai_service.py          # IA orchestration
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── build_service.py       # Builds logic (memory)
│   │   ├── build_service_db.py    # Builds DB service ✅
│   │   ├── email_service.py       # Email notifications
│   │   ├── gw2_api_client.py      # GW2 API integration
│   │   ├── mcm_analytics.py       # McM analytics ✅
│   │   ├── synergy_analyzer.py    # Synergy detection
│   │   ├── team_service.py        # Teams logic (memory)
│   │   ├── team_service_db.py     # Teams DB service ✅
│   │   ├── user_service.py        # User management ✅
│   │   │
│   │   ├── ai/                    # IA Services
│   │   │   ├── chat_service.py
│   │   │   └── ollama_service.py
│   │   │
│   │   ├── exporter/              # Export services
│   │   │   └── snowcrows_exporter.py
│   │   │
│   │   ├── learning/              # Machine Learning
│   │   │   ├── data_collector.py
│   │   │   ├── evaluator.py
│   │   │   ├── pipeline.py
│   │   │   ├── selector.py
│   │   │   ├── storage_manager.py
│   │   │   └── trainer.py
│   │   │
│   │   ├── parser/                # Data parsers
│   │   │   ├── gw2_data.py
│   │   │   └── gw2skill_parser.py
│   │   │
│   │   └── scraper/               # Web scrapers
│   │       └── community_scraper.py
│   │
│   ├── models/                    # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── build.py               # Build schemas + BuildDB ✅
│   │   ├── chat.py                # Chat schemas
│   │   ├── learning.py            # Learning schemas
│   │   ├── team.py                # Team schemas + TeamDB ✅
│   │   ├── token.py               # JWT token schemas
│   │   └── user.py                # User schemas
│   │
│   ├── db/                        # Database Layer
│   │   ├── __init__.py
│   │   ├── base.py                # DB session factory
│   │   ├── base_class.py          # Declarative Base
│   │   ├── init_db.py             # DB initialization
│   │   ├── models.py              # UserDB, LoginHistory ✅
│   │   ├── session.py             # Async sessions
│   │   └── types.py               # GUID custom type ✅
│   │
│   ├── core/                      # Core utilities
│   │   ├── __init__.py
│   │   ├── cache.py               # Redis caching
│   │   ├── circuit_breaker.py    # Circuit breaker pattern
│   │   ├── config.py              # Settings (Pydantic)
│   │   ├── logging.py             # Structured logging
│   │   ├── redis.py               # Redis client
│   │   └── security.py            # JWT + OAuth2 ✅
│   │
│   ├── agents/                    # IA Agents
│   │   └── recommender_agent.py  # Build recommender
│   │
│   ├── workflows/                 # Multi-agent workflows
│   │   ├── base.py
│   │   ├── build_optimization_workflow.py
│   │   ├── learning_workflow.py
│   │   ├── meta_analysis_workflow.py
│   │   └── team_analysis_workflow.py
│   │
│   ├── learning/                  # ML Components
│   │   ├── data/
│   │   │   ├── collector.py
│   │   │   └── storage.py
│   │   ├── models/
│   │   └── utils/
│   │
│   ├── middleware.py              # Request/Response middleware
│   └── exceptions.py              # Custom exceptions
│
├── tests/                         # Test Suite
│   ├── __init__.py
│   ├── conftest.py                # Fixtures pytest ✅
│   ├── test_db_types.py           # Tests GUID ✅
│   │
│   ├── test_api/                  # Tests endpoints
│   ├── test_services/             # Tests services
│   │   ├── test_build_service.py  # 15 tests (fixtures manquantes)
│   │   └── test_team_service.py   # Tests teams
│   └── test_websocket_mcm.py      # Tests WebSocket
│
├── alembic/                       # Migrations DB
│   ├── versions/
│   └── env.py
│
├── requirements.txt               # Dependencies prod
├── requirements-dev.txt           # Dependencies dev
├── pytest.ini                     # Pytest config
└── .env.example                   # Environment variables
```

---

## 🎨 CONVENTIONS DE NOMMAGE

### Models Database (SQLAlchemy)

**Suffix `DB`** pour distinguer des schémas Pydantic:

```python
# backend/app/db/models.py
class UserDB(Base):
    __tablename__ = "users"
    
# backend/app/models/build.py
class BuildDB(Base):
    __tablename__ = "builds"
    
# backend/app/models/team.py
class TeamCompositionDB(Base):
    __tablename__ = "team_compositions"
    
class TeamSlotDB(Base):
    __tablename__ = "team_slots"
```

### Schemas Pydantic

**Suffixes sémantiques**:

```python
# backend/app/models/user.py
class UserBase(BaseModel):      # Champs communs
class UserCreate(UserBase):     # Création
class UserUpdate(BaseModel):    # Update partiel
class UserOut(UserBase):        # Réponse API
class UserLogin(BaseModel):     # Login

# backend/app/models/build.py
class Build(BaseModel):         # Schema principal
class BuildCreate(BaseModel):   # Création
class BuildUpdate(BaseModel):   # Update
class BuildResponse(BaseModel): # Réponse enrichie
```

### Services

**Pattern `{Entity}Service`**:

```python
# backend/app/services/build_service_db.py
class BuildService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_build(self, data: BuildCreate, user: UserDB) -> Build:
        ...
```

### Endpoints

**RESTful + version**:

```python
# backend/app/api/builds_db.py
router = APIRouter()

@router.post("/builds", response_model=Build, status_code=201)
async def create_build(...):
    ...

@router.get("/builds/{build_id}", response_model=Build)
async def get_build(...):
    ...
```

---

## 🗄️ MODÈLES DE DONNÉES

### UserDB (Authentication)

```python
class UserDB(Base):
    """User model for authentication and profile."""
    __tablename__ = "users"
    
    # Primary Key (GUID cross-database)
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Profile
    full_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    preferences = Column(JSON, nullable=True, default=dict)
    
    # Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    builds = relationship("BuildDB", back_populates="user", cascade="all, delete-orphan")
    team_compositions = relationship("TeamCompositionDB", back_populates="user", cascade="all, delete-orphan")
```

### BuildDB (Builds Persistence)

```python
class BuildDB(Base):
    """SQLAlchemy model for Build persistence."""
    __tablename__ = "builds"
    
    # Primary Key
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    profession: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    game_mode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # JSON fields (complex data)
    trait_lines: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    equipment: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    synergies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    counters: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Stats
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="builds")
```

### TeamCompositionDB (Teams)

```python
class TeamCompositionDB(Base):
    """SQLAlchemy model for Team Composition persistence."""
    __tablename__ = "team_compositions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    game_mode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Team data
    total_dps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_healing: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_toughness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Visibility
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="team_compositions")
    team_slots: Mapped[List["TeamSlotDB"]] = relationship(
        "TeamSlotDB", back_populates="team_composition", cascade="all, delete-orphan"
    )
```

---

## 🔌 SERVICES ARCHITECTURE

### Pattern Repository

```python
class BuildService:
    """Service for managing builds with database persistence."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_build(self, data: BuildCreate, user: UserDB) -> Build:
        """Create new build in database."""
        db_build = BuildDB(
            **data.model_dump(),
            user_id=user.id
        )
        self.db.add(db_build)
        await self.db.commit()
        await self.db.refresh(db_build)
        return Build.model_validate(db_build)
    
    async def get_build(self, build_id: str, user: Optional[UserDB] = None) -> Build:
        """Get build by ID with permission check."""
        stmt = select(BuildDB).where(BuildDB.id == build_id)
        result = await self.db.execute(stmt)
        db_build = result.scalar_one_or_none()
        
        if not db_build:
            raise HTTPException(status_code=404, detail="Build not found")
        
        # Permission check
        if not db_build.is_public and (not user or db_build.user_id != user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return Build.model_validate(db_build)
```

### Dependency Injection

```python
# backend/app/api/builds_db.py

async def get_current_user(...) -> UserDB:
    """Dependency: Get authenticated user."""
    ...

async def get_db() -> AsyncSession:
    """Dependency: Get database session."""
    ...

@router.post("/builds", response_model=Build)
async def create_build(
    build_data: BuildCreate,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Build:
    service = BuildService(db)
    return await service.create_build(build_data, current_user)
```

---

## 🔐 SÉCURITÉ

### Authentication Flow

```
1. User Login (POST /api/v1/auth/login)
   ↓
2. Verify credentials (UserService)
   ↓
3. Generate JWT tokens (access + refresh)
   ↓
4. Return tokens to client
   ↓
5. Client includes token in header
   ↓
6. Verify token (OAuth2PasswordBearer)
   ↓
7. Extract user from token
   ↓
8. Inject UserDB in endpoint (Depends)
```

### JWT Configuration

```python
# backend/app/core/security.py

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

## 📝 RECOMMANDATIONS

### 1. Migration Complète vers DB Services

**Actuellement**: Mix services mémoire + DB

**À faire**:
- Deprecate `build_service.py` (mémoire)
- Standardiser sur `build_service_db.py`
- Idem pour teams

### 2. Type Hints Partout

**Actuel**: Certains services sans types

**À faire**:
```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

async def list_builds(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100
) -> List[Build]:
    ...
```

### 3. Agents IA Structure

**Créer base commune**:
```python
# backend/app/agents/base.py
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, context: dict) -> dict:
        pass
```

---

[← Solution UUID](./01_SOLUTION_UUID.md) | [Index](./00_INDEX.md) | [Tests →](./03_TESTS_COVERAGE.md)
