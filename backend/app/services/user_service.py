"""
User Service Layer

This module provides the business logic for user-related operations,
acting as an intermediary between the API endpoints and the database models.
"""

from datetime import datetime, timedelta
import os
from typing import Optional, Dict, Any

from fastapi import Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

import bcrypt

from app.core.config import settings
from app.db.models import UserDB as User, LoginHistory


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _is_testing_mode() -> bool:
    """Determine if the application is running under test conditions."""
    override = os.getenv("GW2OPTIMIZER_TESTING_OVERRIDE")
    if override is not None:
        return override.lower() in {"1", "true", "yes"}

    if "TESTING" in os.environ:
        value = os.getenv("TESTING", "").lower()
        if value:
            return value in {"1", "true", "yes"}

    if os.getenv("PYTEST_CURRENT_TEST"):
        return True

    return bool(getattr(settings, "TESTING", False))


class UserService:
    """Service for handling user-related logic."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by their ID."""
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get a user by their username."""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create_user(self, email: str, username: str, hashed_password: str) -> User:
        """Create a new user in the database."""
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            preferences={},
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def handle_failed_login(self, email: str) -> None:
        """Increment failed login attempts and lock account if necessary."""
        user = await self.get_by_email(email)
        if user and user.is_active:
            user.failed_login_attempts += 1
            reached_threshold = user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS
            testing_mode = _is_testing_mode()
            enforce_lock = settings.ENFORCE_ACCOUNT_LOCKS_IN_TESTS if testing_mode else True

            if reached_threshold and enforce_lock:
                user.is_active = False
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.ACCOUNT_LOCK_DURATION_MINUTES)
            await self.db.commit()  # Commit immediately to lock the user or record the attempt

    async def reset_failed_login_attempts(self, email: str) -> None:
        """Reset failed login attempts for a user."""
        user = await self.get_by_email(email)
        if user and user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            await self.db.commit()

    async def update_password(self, user: User, new_password_hash: str) -> None:
        """Update a user's password."""
        async with self.db.begin_nested():
            user.hashed_password = new_password_hash
            await self.db.flush()

    async def update_user(self, user: User, data: Dict[str, Any]) -> User:
        """Update user profile information."""
        for field, value in data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_preferences(self, user: User, preferences: Dict[str, Any]) -> User:
        """Update user preferences."""
        user.preferences = {**(user.preferences or {}), **preferences}
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def verify_user_email(self, user: User) -> None:
        """Mark a user's email as verified."""
        if not user.is_verified:
            async with self.db.begin_nested():
                user.is_verified = True
                await self.db.flush()

    async def log_login_history(self, user: User, request: Request) -> None:
        """Log a successful login event."""
        login_record = LoginHistory(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "N/A"),
            success=True,
        )
        self.db.add(login_record)
        await self.db.commit()

    async def get_login_history(self, user: User, limit: int = 10) -> list[LoginHistory]:
        """Get the recent login history for a user."""
        result = await self.db.execute(
            select(LoginHistory)
            .where(LoginHistory.user_id == user.id)
            .order_by(desc(LoginHistory.login_timestamp))
            .limit(limit)
        )
        return result.scalars().all()
