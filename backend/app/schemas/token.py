"""Pydantic models for JWT tokens."""

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field


class TokenBase(BaseModel):
    """Base token model."""
    token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: Optional[Union[str, int]] = Field(None, description="Subject (user ID)")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    iat: Optional[datetime] = Field(None, description="Issued at time")
    is_active: bool = Field(True, description="Whether the user is active")
    is_superuser: bool = Field(False, description="Whether the user is a superuser")


class Token(TokenBase):
    """Token response model."""
    pass


class TokenData(BaseModel):
    """Token data model."""
    sub: Optional[str] = Field(None, description="Subject (user ID)")
    jti: Optional[str] = Field(None, description="JWT ID")
    username: Optional[str] = Field(None, description="Username")
    scopes: list[str] = Field(default_factory=list, description="List of scopes")
