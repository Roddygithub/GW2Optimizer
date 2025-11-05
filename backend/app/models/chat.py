"""Chat models."""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single chat message."""

    role: MessageRole = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp of the message")

    @validator("content")
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., min_length=1, max_length=2000, description="The user's message")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list, description="Previous messages in the conversation"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the conversation")
    version: str = Field(..., description="Client application version")

    @validator("conversation_history")
    def validate_history(cls, v):
        for msg in v:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each message must have 'role' and 'content' fields")
            if msg["role"] not in ["user", "assistant", "system"]:
                raise ValueError("Message role must be one of: 'user', 'assistant', 'system'")
        return v


class BuildSuggestion(BaseModel):
    """Build suggestion model."""

    id: Optional[str] = Field(None, description="Unique identifier for the build")
    name: Optional[str] = Field(None, description="Name of the build")
    profession: Optional[str] = Field(None, description="Profession name")
    role: Optional[str] = Field(None, description="Role in the team composition")
    weapons: Optional[Dict[str, str]] = Field(None, description="Weapons used in the build")
    traits: Optional[List[str]] = Field(None, description="List of traits")
    skills: Optional[List[str]] = Field(None, description="List of skills")
    stats: Optional[Dict[str, int]] = Field(None, description="Character stats")
    player_count: Optional[int] = Field(None, description="Number of players using this build")
    gw2skills_url: Optional[str] = Field(
        None, description="GW2Skills URL for the build (e.g., https://gw2skills.net/editor/abc123)"
    )

    @validator("gw2skills_url")
    def validate_gw2skills_url(cls, v):
        if v is None:
            return v

        # Check if it's a valid URL
        import re

        pattern = r"^https?://(?:en\.)?gw2skills\.net/editor/[\w-]+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid GW2Skills URL format. Expected format: https://gw2skills.net/editor/...")

        return v


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="The assistant's response message")
    suggestions: List[str] = Field(default_factory=list, description="List of suggested follow-up questions or actions")
    builds: List[BuildSuggestion] = Field(default_factory=list, description="List of build suggestions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the response")
    action_required: Optional[str] = Field(
        None, description="Action required from the user (e.g., 'parse_build', 'optimize_team')"
    )

    class Config:
        schema_extra = {
            "example": {
                "response": "Here's a great build for your Guardian in WvW zergs...",
                "suggestions": [
                    "Show me a DPS build instead",
                    "What about a support Firebrand?",
                    "How should I play this build?",
                ],
                "builds": [
                    {
                        "name": "Heal Firebrand",
                        "profession": "Guardian",
                        "role": "Heal/Support",
                        "gw2skills_url": "https://lulz.me/abc123",
                    }
                ],
                "metadata": {
                    "response_time": 1.23,
                    "model_used": "llama3",
                    "tokens_generated": 145,
                    "timestamp": "2025-04-15T12:00:00Z",
                },
                "action_required": None,
            }
        }
