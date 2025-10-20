"""Chat models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single chat message."""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    """Chat request."""

    message: str
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    context: Optional[str] = None  # Additional context (current team, builds, etc.)


class ChatResponse(BaseModel):
    """Chat response."""

    response: str
    suggestions: List[str] = Field(default_factory=list)
    builds_mentioned: List[str] = Field(default_factory=list)  # URLs or IDs
    action_required: Optional[str] = None  # "parse_build", "optimize_team", etc.
