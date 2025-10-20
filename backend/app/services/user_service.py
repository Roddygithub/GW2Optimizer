"""
User Service Layer

This module provides the business logic for user-related operations,
acting as an intermediary between the API endpoints and the database models.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from passlib.context import CryptContext

from app.core.config import settings
from app.db.models import User, LoginHistory

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


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
        )
        async with self.db.begin_nested():
            self.db.add(new_user)
            await self.db.flush()
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
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.is_active = False
                user.locked_at = datetime.utcnow()
            await self.db.commit() # Commit immediately to lock the user

    async def reset_failed_login_attempts(self, email: str) -> None:
        """Reset failed login attempts for a user."""
        user = await self.get_by_email(email)
        if user and user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            # This will be committed along with the login history log

    async def update_password(self, user: User, new_password_hash: str) -> None:
        """Update a user's password."""
        async with self.db.begin_nested():
            user.hashed_password = new_password_hash
            await self.db.flush()

    async def update_user(self, user: User, data: Dict[str, Any]) -> User:
        """Update user profile information."""
        async with self.db.begin_nested():
            for field, value in data.items():
                setattr(user, field, value)
            await self.db.flush()
            await self.db.refresh(user)
            return user

    async def update_preferences(self, user: User, preferences: Dict[str, Any]) -> User:
        """Update user preferences."""
        async with self.db.begin_nested():
            # Merge new preferences with existing ones
            user.preferences = {**(user.preferences or {}), **preferences}
            await self.db.flush()
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
        async with self.db.begin_nested():
            login_record = LoginHistory(
                user_id=user.id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", "N/A"),
            )
            self.db.add(login_record)
            await self.db.flush()

    async def get_login_history(self, user: User, limit: int = 10) -> list[LoginHistory]:
        """Get the recent login history for a user."""
        result = await self.db.execute(
            select(LoginHistory)
            .where(LoginHistory.user_id == user.id)
            .order_by(desc(LoginHistory.login_timestamp))
            .limit(limit)
        )
        return result.scalars().all()