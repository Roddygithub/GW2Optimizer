"""Data models."""

from app.models.build import Build, BuildCreate, BuildResponse, BuildDB
from app.models.team import TeamComposition, TeamResponse, TeamCompositionDB, TeamSlotDB
from app.models.chat import ChatMessage, ChatRequest, ChatResponse
from app.db.models import UserDB as User, LoginHistory
from app.models.user import UserCreate, UserLogin, UserOut, UserUpdate
from app.models.token import Token, TokenData
from app.models.gw2.entities import (
    Profession,
    Specialization,
    Trait,
    Skill,
    Weapon,
    Item,
    Build as GW2Build,
)

__all__ = [
    # Build models
    "Build",
    "BuildCreate",
    "BuildResponse",
    "BuildDB",
    # Team models
    "TeamComposition",
    "TeamResponse",
    "TeamCompositionDB",
    "TeamSlotDB",
    # Chat models
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    # User models
    "User",
    "UserCreate",
    "UserLogin",
    "UserOut",
    "UserUpdate",
    # Auth models
    "Token",
    "TokenData",
    # GW2 domain models
    "Profession",
    "Specialization",
    "Trait",
    "Skill",
    "Weapon",
    "Item",
    "GW2Build",
    "TeamComposition",
    "TeamResponse",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
]
