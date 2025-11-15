"""
Pydantic schemas for User data.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import uuid
import re


if TYPE_CHECKING:
    from app.db.models import UserDB
else:
    # Runtime import for backward compatibility
    try:
        from app.db.models import UserDB
    except ImportError:
        UserDB = None  # type: ignore


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's unique email address.", example="user@example.com")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="User's unique username. Must be alphanumeric with underscores.",
        example="player_123",
    )


COMMON_PASSWORDS = {"password", "123456", "qwerty", "azerty", "123456789", "password123"}


class UserCreate(UserBase):
    password: str = Field(
        ...,
        description="User's password. Must be at least 12 characters long and contain uppercase, lowercase, a digit, and a special character.",
        example="ValidPass!123",
    )

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str, info: FieldValidationInfo) -> str:
        """Validate password complexity with user-friendly messages."""
        if len(v) < 12:
            raise ValueError("Le mot de passe doit contenir au moins 12 caractères.")

        errors = []
        if not re.search(r"[A-Z]", v):
            errors.append("au moins une lettre majuscule")
        if not re.search(r"[a-z]", v):
            errors.append("au moins une lettre minuscule")
        if not re.search(r"\d", v):
            errors.append("au moins un chiffre")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("au moins un caractère spécial")

        if errors:
            raise ValueError(f"Le mot de passe doit contenir {', '.join(errors)}.")

        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("Ce mot de passe est trop courant et ne peut pas être utilisé.")

        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    username: Optional[str] = Field(None, description="User's username (optional)")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100, example="John Doe")
    bio: Optional[str] = Field(None, max_length=500, example="Experienced GW2 player.")
    profile_picture_url: Optional[str] = Field(None, example="https://example.com/avatar.png")
    preferences: Optional[Dict[str, Any]] = Field(None, example={"theme": "dark", "language": "en"})


class UserPreferencesUpdate(BaseModel):
    preferences: Dict[str, Any] = Field(..., example={"theme": "dark", "notifications_enabled": True})


class UserOut(UserBase):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    preferences: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class LoginHistoryOut(BaseModel):
    ip_address: str
    user_agent: str
    login_timestamp: datetime

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


__all__ = [
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "UserLogin",
    "UserDB",
    "UserPreferencesUpdate",
    "LoginHistoryOut",
    "PasswordResetRequest",
    "PasswordReset",
]
