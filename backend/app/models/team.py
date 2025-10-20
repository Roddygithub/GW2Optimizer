"""Team composition models for GW2Optimizer."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.build import Build, GameMode, team_builds

if TYPE_CHECKING:
    from app.models.user import UserDB
    from app.models.build import BuildDB


class TeamSlotDB(Base):
    """SQLAlchemy model for TeamSlot (association object pattern)."""
    
    __tablename__ = "team_slots"
    
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid4())
    )
    
    # Foreign keys
    team_composition_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("team_compositions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    build_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("builds.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Additional attributes
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    player_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    team_composition: Mapped["TeamCompositionDB"] = relationship(
        "TeamCompositionDB",
        back_populates="team_slots"
    )
    build: Mapped["BuildDB"] = relationship("BuildDB")
    
    def __repr__(self) -> str:
        return f"<TeamSlotDB(id={self.id}, slot_number={self.slot_number})>"


class TeamSlot(BaseModel):
    """Team slot with build assignment."""
    
    model_config = ConfigDict(from_attributes=True)
    
    slot_number: int = Field(ge=1, le=50)
    build: Build
    player_name: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=1, ge=1, le=5)


class TeamSynergy(BaseModel):
    """Team synergy analysis."""

    synergy_type: str  # "boons", "combo_fields", "cc", "healing"
    description: str
    involved_slots: List[int]
    strength: float = Field(ge=0, le=10)


class TeamCompositionDB(Base):
    """SQLAlchemy model for TeamComposition."""
    
    __tablename__ = "team_compositions"
    
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    game_mode: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    team_size: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # JSON fields for complex data
    synergies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    strengths: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Foreign Keys
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="team_compositions")
    team_slots: Mapped[List["TeamSlotDB"]] = relationship(
        "TeamSlotDB",
        back_populates="team_composition",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<TeamCompositionDB(id={self.id}, name={self.name}, team_size={self.team_size})>"


class TeamCompositionBase(BaseModel):
    """Base model for TeamComposition with shared attributes."""
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    game_mode: GameMode
    team_size: int = Field(ge=1, le=50, description="Team size")
    description: Optional[str] = Field(None, description="Team description")
    is_public: bool = Field(default=False, description="Whether team is public")


class TeamComposition(TeamCompositionBase):
    """Complete team composition model for API responses."""
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    # Team Slots
    slots: List[TeamSlot] = Field(default_factory=list)
    
    # Analysis
    synergies: List[TeamSynergy] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    overall_rating: Optional[float] = Field(None, ge=0, le=10)


class TeamCompositionCreate(TeamCompositionBase):
    """Create team composition request."""
    
    build_ids: List[str] = Field(
        default_factory=list,
        description="List of build IDs to include in the team"
    )


class TeamCompositionUpdate(BaseModel):
    """Update team composition request."""
    
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    overall_rating: Optional[float] = Field(None, ge=0, le=10)


class TeamResponse(BaseModel):
    """Team composition response with AI analysis."""
    
    model_config = ConfigDict(from_attributes=True)
    
    team: TeamComposition
    ai_recommendations: Optional[Dict[str, str]] = Field(default=None, description="AI recommendations")
    alternative_compositions: List[TeamComposition] = Field(default_factory=list, description="Alternative compositions")


class TeamOptimizeRequest(BaseModel):
    """Request to optimize a team composition."""
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "game_mode": "zerg",
                "team_size": 15,
                "required_roles": {"healer": 2, "support": 3, "dps": 10},
                "existing_builds": ["550e8400-e29b-41d4-a716-446655440000"],
                "constraints": "Need at least 2 sources of stability and 3 sources of might"
            }
        }
    )
    
    game_mode: GameMode
    team_size: int = Field(ge=1, le=50, description="Team size")
    required_roles: Dict[str, int] = Field(
        default_factory=dict,
        description="Mapping of role names to count required"
    )
    existing_builds: List[str] = Field(
        default_factory=list,
        description="List of build IDs to include in the optimization"
    )
    constraints: Optional[str] = Field(
        None,
        description="Additional constraints in natural language"
    )
