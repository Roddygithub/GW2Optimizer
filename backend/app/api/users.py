"""User profile API endpoints.

This module handles operations related to the current authenticated user:
profile, preferences, and login history.
"""


from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.db.models import UserDB as User
from app.models.user import (
    UserOut,
    UserUpdate,
    UserPreferencesUpdate,
    LoginHistoryOut,
)
from app.services.user_service import UserService


router = APIRouter(tags=["Users"])


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user details",
    description="Get details of the currently authenticated user.",
    responses={
        200: {"description": "Current user details"},
        401: {"description": "Not authenticated"},
    },
)
async def read_users_me(current_user: User = Depends(get_current_active_user)) -> UserOut:
    """Get the currently authenticated user's details."""
    return current_user


@router.patch(
    "/me",
    response_model=UserOut,
    summary="Patch current user profile",
    description="Partially update profile information for the authenticated user.",
)
async def patch_user_me(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    """Partially update the current user's profile."""

    # Update only non-None fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    logger.info(f"User profile updated: {current_user.email}")
    return current_user


@router.put(
    "/me",
    response_model=UserOut,
    summary="Update current user profile",
    description="Update profile information for the authenticated user.",
)
async def update_user_me(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    """Completely update the current user's profile."""
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user, update_data.model_dump(exclude_unset=True))
    return updated_user


@router.put(
    "/me/preferences",
    response_model=UserOut,
    summary="Update user preferences",
    description="Update preferences for the authenticated user.",
)
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserOut:
    """Update the current user's stored preferences."""
    user_service = UserService(db)
    updated_user = await user_service.update_preferences(current_user, preferences_update.preferences)
    return updated_user


@router.get(
    "/me/login-history",
    response_model=list[LoginHistoryOut],
    summary="Get recent login history",
    description="Retrieve recent login attempts for the authenticated user.",
)
async def get_login_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[LoginHistoryOut]:
    """Return the recent login history for the current user."""
    user_service = UserService(db)
    history = await user_service.get_login_history(current_user)
    if not history:
        await user_service.log_login_history(current_user, request)
        history = await user_service.get_login_history(current_user)
    return [LoginHistoryOut.model_validate(h) for h in history]
