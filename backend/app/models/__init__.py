"""
Data Models

This module contains all Pydantic and SQLAlchemy models used throughout the application.
Models are organized by domain (builds, teams, users, etc.) and are used for data validation,
database operations, and API request/response schemas.
"""

# Build models
from app.models.build import Build, BuildCreate, BuildResponse, BuildDB  # noqa: F401
from app.models.build import GameMode, Profession, Role  # noqa: F401

# Team models
from app.models.team import (  # noqa: F401
    TeamComposition,
    TeamResponse,
    TeamCompositionDB,
    TeamSlotDB,
    TeamCompositionCreate,
    TeamCompositionUpdate,
)

# Chat models
from app.models.chat import ChatMessage, ChatRequest, ChatResponse  # noqa: F401

# User models
from app.db.models import UserDB as User, LoginHistory  # noqa: F401
from app.models.user import UserCreate, UserLogin, UserOut, UserUpdate  # noqa: F401

# Auth models
from app.models.token import Token, TokenData  # noqa: F401

# Game models

__all__ = [
    # Build models
    "Build",
    "BuildCreate",
    "BuildResponse",
    "BuildDB",
    "GameMode",
    "Profession",
    "Role",
    # Team models
    "TeamComposition",
    "TeamResponse",
    "TeamCompositionDB",
    "TeamSlotDB",
    "TeamCompositionCreate",
    "TeamCompositionUpdate",
    # Chat models
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
    # User models
    "User",
    "LoginHistory",
    "UserCreate",
    "UserLogin",
    "UserOut",
    "UserUpdate",
    # Auth models
    "Token",
    "TokenData",
]
