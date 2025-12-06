from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StrategySlot(BaseModel):
    """Strategic slot description produced by TeamStrategyAgent."""

    model_config = ConfigDict(from_attributes=True)

    index: int = Field(ge=0)
    group_index: int = Field(ge=1)
    role: str
    profession: str
    specialization: str
    weapon_preference: Optional[str] = None
    playstyle: Optional[str] = None
    notes: Optional[str] = None


class StrategyGroup(BaseModel):
    """Group of strategy slots (e.g. subgroup of a squad)."""

    model_config = ConfigDict(from_attributes=True)

    index: int = Field(ge=1)
    label: Optional[str] = None
    slots: List[StrategySlot]


class TeamStrategyPlan(BaseModel):
    """High-level team strategy plan returned by the LLM strategist."""

    model_config = ConfigDict(from_attributes=True)

    mode: str
    team_size: int = Field(ge=1, le=50)
    groups: List[StrategyGroup]
    global_concept: Optional[str] = None
    high_level_notes: List[str] = Field(default_factory=list)


class TeamStrategyRequest(BaseModel):
    """Input payload for TeamStrategyAgent."""

    message: str
    explicit_mode: Optional[str] = None
    explicit_experience: Optional[str] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
