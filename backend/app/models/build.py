"""Build models for GW2Optimizer."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.types import GUID

if TYPE_CHECKING:
    from app.models.user import UserDB
    from app.models.team import TeamCompositionDB


class Profession(str, Enum):
    """GW2 Professions."""

    GUARDIAN = "Guardian"
    REVENANT = "Revenant"
    WARRIOR = "Warrior"
    ENGINEER = "Engineer"
    RANGER = "Ranger"
    THIEF = "Thief"
    ELEMENTALIST = "Elementalist"
    MESMER = "Mesmer"
    NECROMANCER = "Necromancer"


class GameMode(str, Enum):
    """GW2 Game Modes."""

    ROAMING = "roaming"
    RAID_GUILD = "raid_guild"
    ZERG = "zerg"


class Role(str, Enum):
    """Team Roles."""

    TANK = "tank"
    DPS = "dps"
    SUPPORT = "support"
    HEALER = "healer"
    BOONSHARE = "boonshare"
    UTILITY = "utility"


class TraitLine(BaseModel):
    """Trait line configuration."""

    id: int
    name: str
    traits: List[int] = Field(default_factory=list, max_length=3)


class Skill(BaseModel):
    """Skill configuration."""

    slot: str
    id: int
    name: str


class Equipment(BaseModel):
    """Equipment slot."""

    slot: str
    id: int
    name: str
    stats: Optional[str] = None
    rune_or_sigil: Optional[int] = None


# Association table for many-to-many relationship between TeamComposition and Build
team_builds = Table(
    "team_builds",
    Base.metadata,
    Column("team_composition_id", String, ForeignKey("team_compositions.id", ondelete="CASCADE"), primary_key=True),
    Column("build_id", String, ForeignKey("builds.id", ondelete="CASCADE"), primary_key=True),
    Column("slot_number", Integer, nullable=False),
    Column("player_name", String(100), nullable=True),
    Column("priority", Integer, default=1, nullable=False),
)


class BuildDB(Base):
    """SQLAlchemy model for Build persistence."""

    __tablename__ = "builds"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    profession: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    game_mode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # JSON fields for complex data
    trait_lines: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    equipment: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    synergies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    counters: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    playstyle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Ratings
    effectiveness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Foreign Keys
    user_id: Mapped[str] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="builds")

    def __repr__(self) -> str:
        return f"<BuildDB(id={self.id}, name={self.name}, profession={self.profession})>"


class BuildBase(BaseModel):
    """Base model for Build with shared attributes."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=100, description="Build name")
    profession: Profession
    specialization: Optional[str] = Field(None, max_length=100)
    game_mode: GameMode
    role: Role
    description: Optional[str] = Field(None, description="Build description")
    playstyle: Optional[str] = Field(None, description="Playstyle description")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL")
    source_type: Optional[str] = Field(None, max_length=50, description="Source type")
    effectiveness: Optional[float] = Field(None, ge=0, le=10, description="Effectiveness rating")
    difficulty: Optional[int] = Field(None, ge=1, le=5, description="Difficulty rating")
    is_public: bool = Field(default=False, description="Whether build is public")


class Build(BuildBase):
    """Complete build model for API responses."""

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    # Build Configuration
    trait_lines: List[TraitLine] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    equipment: List[Equipment] = Field(default_factory=list)
    synergies: List[str] = Field(default_factory=list)
    counters: List[str] = Field(default_factory=list)


class BuildCreate(BuildBase):
    """Create build request."""

    trait_lines: List[TraitLine] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    equipment: List[Equipment] = Field(default_factory=list)
    synergies: List[str] = Field(default_factory=list)
    counters: List[str] = Field(default_factory=list)
    gw2skill_url: Optional[HttpUrl] = Field(None, description="GW2Skill URL to parse")
    custom_requirements: Optional[str] = Field(None, description="Custom AI requirements")


class BuildUpdate(BaseModel):
    """Update build request."""

    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    playstyle: Optional[str] = None
    is_public: Optional[bool] = None
    effectiveness: Optional[float] = Field(None, ge=0, le=10)
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    trait_lines: Optional[List[TraitLine]] = None
    skills: Optional[List[Skill]] = None
    equipment: Optional[List[Equipment]] = None
    synergies: Optional[List[str]] = None
    counters: Optional[List[str]] = None


class BuildResponse(BaseModel):
    """Build response with AI analysis."""

    model_config = ConfigDict(from_attributes=True)

    build: Build
    ai_analysis: Optional[Dict[str, str]] = Field(default=None, description="AI analysis")
    similar_builds: List[Build] = Field(default_factory=list, description="Similar builds")
