"""
Authentication API endpoints.

This module handles user authentication, registration, and token management.
It provides endpoints for user registration, email verification, login, token refresh, password reset, and user profile management.
"""

from collections import defaultdict, deque
from datetime import timedelta
from functools import wraps
import os
import time
from typing import Optional, Callable, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import logger
from jwt import InvalidTokenError as JWTError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
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
    UserUpdate,
    UserPreferencesUpdate,
    PasswordReset,
    LoginHistoryOut,
)
from app.services.user_service import UserService
from app.services.email_service import send_password_reset_email, send_verification_email

router = APIRouter(tags=["Authentication"])


def _is_testing() -> bool:
    return bool(os.getenv("PYTEST_CURRENT_TEST"))


def rate_limit_key(request: Request) -> str:
    """Return a rate-limit key that isolates pytest runs from each other."""
    if _is_testing():
        current_test = os.getenv("PYTEST_CURRENT_TEST")
        if current_test:
            client_host = request.client.host if request.client else "unknown"
            return f"{current_test}:{client_host}"
    return get_remote_address(request)


limiter = Limiter(key_func=rate_limit_key, default_limits=[settings.DEFAULT_RATE_LIMIT])
_test_rate_state: defaultdict[tuple[str, str], deque[float]] = defaultdict(deque)


def _parse_rate_limit(limit: str) -> tuple[int, float]:
    try:
        count_str, period = limit.split("/")
        count = int(count_str)
    except ValueError as exc:
        raise ValueError(f"Invalid rate limit format: {limit}") from exc

    period = period.strip().lower()
    if period in {"second", "seconds"}:
        window = 1.0
    elif period in {"minute", "minutes"}:
        window = 60.0
    elif period in {"hour", "hours"}:
        window = 3600.0
    elif period in {"day", "days"}:
        window = 86400.0
    else:
        raise ValueError(f"Unsupported rate limit period: {period}")

    return count, window


def rate_limit(limit: Optional[str]) -> Callable[[Callable], Callable]:
    if limit is None:
        return lambda func: func

    if _is_testing():
        count, window = _parse_rate_limit(limit)

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                request: Optional[Request] = kwargs.get("request")
                if request is None:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break

                if request is None:
                    return await func(*args, **kwargs)

                key = (
                    os.getenv("PYTEST_CURRENT_TEST", "unknown_test"),
                    request.url.path,
                )
                now = time.monotonic()
                bucket = _test_rate_state[key]

                while bucket and now - bucket[0] >= window:
                    bucket.popleft()

                if len(bucket) >= count:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too Many Requests")

                bucket.append(now)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    return limiter.limit(limit)


def _cookie_options(max_age: int | None = None) -> dict:
    """Build standard cookie options based on settings."""

    options: dict[str, object] = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE.lower(),
    }

    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN

    if max_age is not None:
        options["max_age"] = max_age
    elif settings.COOKIE_MAX_AGE is not None:
        options["max_age"] = settings.COOKIE_MAX_AGE

    return options


def _set_auth_cookie(response: Response, value: str, max_age: int | None) -> None:
    """Apply standard auth cookie settings."""

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=value,
        **_cookie_options(max_age=max_age),
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear the auth cookie using the configured options."""

    options = _cookie_options(max_age=0)
    cookie_parts: list[str] = [
        f"{settings.ACCESS_TOKEN_COOKIE_NAME}=",
        "Path=/",
        'expires="Thu, 01 Jan 1970 00:00:00 GMT"',
        "Max-Age=0",
    ]

    if options.pop("httponly", False):
        cookie_parts.append("HttpOnly")

    samesite = options.pop("samesite", None)
    if isinstance(samesite, str) and samesite:
        cookie_parts.append(f"SameSite={samesite.capitalize()}")

    if options.pop("secure", False):
        cookie_parts.append("Secure")

    domain = options.pop("domain", None)
    if isinstance(domain, str) and domain:
        cookie_parts.append(f"Domain={domain}")

    # max_age already captured above
    options.pop("max_age", None)

    existing_vary = response.headers.get("Vary")
    if existing_vary:
        vary_values = [value.strip() for value in existing_vary.split(",") if value.strip()]
        if not any(value.lower() == "set-cookie" for value in vary_values):
            vary_values.append("set-cookie")
            response.headers["Vary"] = ", ".join(vary_values)
    else:
        response.headers["Vary"] = "set-cookie"
    response.headers.append("set-cookie", "; ".join(cookie_parts))


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
        raise UserEmailExistsException(detail=f"Email '{user_in.email}' already exists")

    existing_username = await user_service.get_by_username(user_in.username)
    if existing_username:
        logger.warning(f"Registration failed: username '{user_in.username}' already taken.")
        raise UserUsernameExistsException(detail=f"Username '{user_in.username}' already taken")

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
    """Login with email (as username) and password."""
    user_service = UserService(db)
    user = await user_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        # Handle failed attempt and potential account lock
        await user_service.handle_failed_login(form_data.username)
        logger.warning(
            "Failed login attempt",
            extra={
                "email": form_data.username,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent"),
            },
        )
        raise InvalidCredentialsException()

    if not user.is_active:
        logger.warning(
            "Login attempt for inactive/locked user",
            extra={
                "email": user.email,
                "ip": request.client.host if request.client else "unknown",
            },
        )
        raise AccountLockedException()

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
    return await login_for_access_token(response, request, form_data, db)  # type: ignore[no-any-return]


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
    user_service = UserService(db)
    history = await user_service.get_login_history(current_user)
    if not history:
        await user_service.log_login_history(current_user, request)
        history = await user_service.get_login_history(current_user)
    return [LoginHistoryOut.model_validate(h) for h in history]


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
    redis: Redis = Depends(get_redis_client),
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
