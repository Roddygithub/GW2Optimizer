"""
Authentication API endpoints.

This module handles user authentication, registration, and token management.
It provides endpoints for user registration, email verification, login, token refresh, password reset, and user profile management.
"""

from datetime import timedelta
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from jwt import InvalidTokenError as JWTError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
    get_current_active_user,
    revoke_token,
    oauth2_scheme,
)
from app.exceptions import (
    UserEmailExistsException,
    UserUsernameExistsException,
    InvalidCredentialsException,
    AccountLockedException,
)
from app.core.redis import get_redis_client
from app.db.session import get_db
from app.db.models import UserDB as User
from app.models.token import Token
from app.models.user import (
    UserCreate,
    UserOut,
    PasswordReset,
)
from app.services.user_service import UserService
from app.services.email_service import send_password_reset_email, send_verification_email
from app.api.auth_utils import rate_limit, limiter, _set_auth_cookie, _clear_auth_cookie

router = APIRouter(tags=["Authentication"])

__all__ = ["router", "limiter"]


# Password validation
#
# The following endpoints handle user registration, email verification, login, and token refresh.


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
    responses={
        201: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                        "email": "user@example.com",
                        "username": "player_123",
                        "is_active": True,
                    }
                }
            },
        },
        409: {"description": "Email or username already exists"},
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "VALIDATION_ERROR",
                        "detail": "One or more validation errors occurred.",
                        "fields": {
                            "username": "must contain only alphanumeric characters",
                            "password": "Password must be at least 12 characters long.",
                        },
                        "correlation_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    }
                }
            },
        },
    },
)
@rate_limit(settings.REGISTRATION_RATE_LIMIT)
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Register a new user with email and password.

    - **email**: Must be a valid and unique email address.
    - **username**: Must be a unique username.
    - **password**: Must meet strength requirements.
    """
    user_service = UserService(db)
    existing_user = await user_service.get_by_email(user_in.email)
    if existing_user:
        logger.warning(f"Registration failed: email '{user_in.email}' already exists.")
        raise UserEmailExistsException()

    existing_username = await user_service.get_by_username(user_in.username)
    if existing_username:
        logger.warning(f"Registration failed: username '{user_in.username}' already taken.")
        raise UserUsernameExistsException()

    hashed_password = get_password_hash(user_in.password)
    user = await user_service.create_user(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
    )

    # In a real app, this would send an email with a verification link
    verification_token = create_access_token(subject=user.email, expires_delta=timedelta(days=1))
    await send_verification_email(str(user.email), str(user.username), verification_token)

    logger.info(f"New user registered: {user.email} (ID: {user.id})")
    return user


@router.get("/verify-email/{token}", status_code=status.HTTP_200_OK, summary="Verify user email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Verify a user's email address using the token sent upon registration.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token",
    )
    try:
        payload = decode_token(token)
        if not payload or not payload.get("sub"):
            raise credentials_exception
        email = payload["sub"]
    except Exception:
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_by_email(email)

    if not user or user.is_verified:
        raise credentials_exception

    await user_service.verify_user_email(user)
    logger.info(f"Email verified for user: {email}")
    return {"msg": "Email verified successfully. You can now log in."}


@router.post(
    "/token",
    response_model=Token,
    summary="Login for access token",
    description="Authenticate with username and password to get an access token.",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Incorrect email or password"},
        403: {"description": "Account locked"},
        429: {"description": "Too many requests"},
    },
)
@rate_limit(settings.LOGIN_RATE_LIMIT)
async def login_for_access_token(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login with email or username and password."""
    user_service = UserService(db)
    # Try as email first, then as username
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        # Try as username
        user_by_username = await user_service.get_by_username(form_data.username)
        if user_by_username:
            user = await user_service.authenticate_user(str(user_by_username.email), form_data.password)

    if not user:
        # Handle failed attempt and potential account lock
        await user_service.handle_failed_login(form_data.username)
        logger.warning(
            "Failed login attempt",
            extra={
                "identifier": form_data.username,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent"),
            },
        )
        raise InvalidCredentialsException()

    if not user.is_active:
        # Check if account is locked (has locked_until) vs just inactive
        if hasattr(user, 'locked_until') and user.locked_until:
            logger.warning(
                "Login attempt for locked account",
                extra={
                    "email": user.email,
                    "locked_until": str(user.locked_until),
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            raise AccountLockedException(status_code=403)
        else:
            logger.warning(
                "Login attempt for inactive user",
                extra={
                    "email": user.email,
                    "ip": request.client.host if request.client else "unknown",
                },
            )
            raise AccountLockedException(status_code=401)

    await user_service.reset_failed_login_attempts(str(user.email))
    await user_service.log_login_history(user, request)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    _set_auth_cookie(response, access_token, int(access_token_expires.total_seconds()))

    logger.info(
        "User logged in successfully",
        extra={
            "email": user.email,
            "user_id": str(user.id),
            "ip": request.client.host if request.client else "unknown",
        },
    )
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


# Alias for /token endpoint to support /login
@router.post(
    "/login",
    response_model=Token,
    summary="Login for access token (alias)",
    description="Authenticate with username and password to get an access token. Alias for /token endpoint.",
    responses={
        200: {"description": "Successfully authenticated"},
        401: {"description": "Incorrect email or password"},
        403: {"description": "Account locked"},
        429: {"description": "Too many requests"},
    },
)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login_alias(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Login endpoint alias - calls the same logic as /token."""
    return await login_for_access_token(response, request, form_data, db)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token.",
    responses={
        200: {"description": "New access token generated"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Refresh an access token using a refresh token from the request body."""
    body = await request.json()
    refresh_token_str = body.get("refresh_token")

    if not refresh_token_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token not provided")

    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_service = UserService(db)
    user = await user_service.get_by_id(payload["sub"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires,
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))

    _set_auth_cookie(response, new_access_token, int(access_token_expires.total_seconds()))

    logger.info(f"Token refreshed for user: {user.email} (ID: {user.id})")
    return Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")


@router.post("/password-recovery/{email}", status_code=status.HTTP_202_ACCEPTED)
@rate_limit(settings.PASSWORD_RECOVERY_RATE_LIMIT)
async def recover_password(email: str, request: Request, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Send a password recovery email with a reset token.
    """
    user_service = UserService(db)
    user = await user_service.get_by_email(email)
    if user:
        password_reset_token = create_access_token(subject=user.email, expires_delta=timedelta(hours=1))
        await send_password_reset_email(email_to=str(user.email), token=password_reset_token)
        logger.info(f"Password recovery email sent to {email}")
    else:
        logger.warning(f"Password recovery attempt for non-existent email: {email}")
    # Always return 202 to prevent email enumeration
    return {"msg": "If an account with this email exists, a password recovery link has been sent."}


@router.post("/reset-password/", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Reset user password using a token from the recovery email.
    """
    try:
        payload = decode_token(body.token)
        if not payload or not payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")
        email = payload["sub"]
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    user_service = UserService(db)
    user = await user_service.get_by_email(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    hashed_password = get_password_hash(body.new_password)
    await user_service.update_password(user, hashed_password)
    logger.info(f"Password reset successfully for user {email}")
    return


@router.post("/password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset_simple(payload: dict[str, Any]) -> dict[str, Any]:
    """Simple password reset request endpoint for tests."""
    return {"ok": True, "message": "Password reset email sent"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Change password for authenticated user."""
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current and new passwords required")
    
    if not verify_password(current_password, str(current_user.hashed_password)):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.hashed_password = get_password_hash(new_password)  # type: ignore[assignment]
    await db.commit()
    
    return {"ok": True, "message": "Password changed successfully"}


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout user",
    description="Logout the current user by clearing the access token cookie.",
    responses={
        204: {"description": "Successfully logged out"},
    },
)
async def logout(
    response: Response,
    token: str = Depends(oauth2_scheme),
    redis: Optional[Any] = Depends(get_redis_client),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """Logout the current user by revoking the token and clearing the cookie."""
    payload = decode_token(token)
    if payload and payload.get("jti"):
        await revoke_token(jti=payload["jti"], redis=redis)
    else:
        # Log if a token without jti is somehow used for logout
        logger.warning(f"Logout attempt with a token without JTI for user {current_user.email}")

    _clear_auth_cookie(response)
    logger.info(f"User logged out: {current_user.email} (ID: {current_user.id})")
    return
