from datetime import datetime, timedelta
from typing import Any, Optional, cast
import uuid
import time

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError as JWTError
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from redis.exceptions import RedisError
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import get_db
from app.db.models import UserDB as User
from app.models.token import TokenData
from app.core.redis import get_redis_client, redis_circuit_breaker
from app.core.logging import logger
from app.services.user_service import UserService


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """
    OAuth2PasswordBearer that can read the token from a cookie.
    """

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        if not authorization:
            try:
                authorization = await super().__call__(request)
            except HTTPException as e:
                if not self.auto_error and e.status_code == status.HTTP_401_UNAUTHORIZED:
                    return None
                if e.status_code == status.HTTP_401_UNAUTHORIZED:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                raise e
        return authorization


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=f"{settings.API_V1_STR}/auth/token")
oauth2_optional_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Create a new access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid.uuid4())}  # Add a unique identifier to the token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """
    Create a new refresh token.
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),  # Add a unique identifier to the refresh token
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decodes a JWT token, trying multiple keys for rotation.
    """
    keys = [settings.SECRET_KEY] + settings.OLD_SECRET_KEYS
    for key in keys:
        try:
            payload = cast(dict[str, Any], jwt.decode(token, key, algorithms=[settings.ALGORITHM]))
            return payload
        except JWTError:
            continue
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


async def _resolve_user_from_token(
    token: str,
    db: AsyncSession,
    redis: Any | None,
) -> User:
    def _credentials_exc() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = _credentials_exc()

    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        token_data = TokenData(**payload)
        if token_data.jti is None:
            raise credentials_exception
        if token_data.sub is None:
            raise credentials_exception
    except (JWTError, ValidationError) as e:
        logger.warning(f"JWT decoding/validation failed: {e}")
        raise credentials_exception

    def _token_revoked_exc() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    def _fail_closed_exc() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to verify token revocation",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if redis:
        if redis_circuit_breaker.state == "OPEN":
            logger.warning("Redis circuit breaker OPEN during token check; failing closed")
            redis_circuit_breaker.record_failure()
            raise _fail_closed_exc()

        try:
            start_time = time.time()
            if await redis.sismember("revoked_jti", token_data.jti):
                logger.info("Access token rejected: JTI present in revoked set")
                raise _token_revoked_exc()

            duration = time.time() - start_time
            logger.debug(f"Redis sismember check took {duration:.4f} seconds.")
            redis_circuit_breaker.record_success()
        except HTTPException:
            raise
        except RedisError as err:
            logger.error("Redis error while verifying token revocation: %s", err)
            redis_circuit_breaker.record_failure()
            raise _fail_closed_exc() from err
        except Exception as err:
            logger.error("Unexpected error while verifying token revocation", exc_info=True)
            redis_circuit_breaker.record_failure()
            raise _fail_closed_exc() from err

    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.sub)

    if user is None:
        raise credentials_exception
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    redis: Any | None = Depends(get_redis_client),  # Allow None if Redis is disabled
) -> User:
    """Decode token and return the authenticated user."""

    return await _resolve_user_from_token(token, db, redis)


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(oauth2_optional_scheme),
    redis: Any | None = Depends(get_redis_client),
) -> User | None:
    """Return the current user if present; otherwise None without raising."""

    if not token:
        return None

    try:
        return await _resolve_user_from_token(token, db, redis)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


async def get_current_active_user(
    current_user: Any = Depends(get_current_user),
) -> Any:
    """
    Dependency to get the current user and verify they are active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def revoke_token(jti: str, redis: Any | None) -> None:
    """
    Adds a token's JTI to the revocation list in Redis with an expiration
    time matching the access token's lifetime.
    """
    if not redis:
        logger.warning("Redis is not available. Token revocation is not being performed.")
        return

    if redis_circuit_breaker.state == "OPEN":
        logger.error(f"Circuit is open. Skipping token revocation for JTI {jti}.")
        return

    try:
        start_time = time.time()
        async with redis.pipeline(transaction=True) as pipe:
            await pipe.sadd("revoked_jti", jti)
            # The expiration should be slightly longer than the token's lifetime to be safe.
            await pipe.expire("revoked_jti", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 5)
            await pipe.execute()
        duration = time.time() - start_time
        logger.info(f"Token revocation for JTI {jti} took {duration:.4f} seconds.")
        # In a real metrics system, this would be:
        # metrics.histogram('redis.operation.duration', duration, tags=['operation:revoke'])
        redis_circuit_breaker.record_success()
    except Exception as e:
        logger.error(f"Failed to revoke token JTI {jti} in Redis: {e}", exc_info=True)
        redis_circuit_breaker.record_failure()
