from datetime import datetime, timedelta
from typing import Any, Optional, Set
import uuid
import time

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User
from app.models.token import TokenData
from app.core.redis import get_redis_client, redis_circuit_breaker
from app.core.logging import logger
from app.services.user_service import UserService

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """
    OAuth2PasswordBearer that can read the token from a cookie.
    """

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
        if not authorization:
            try:
                authorization = await super().__call__(request)
            except HTTPException as e:
                if e.status_code == status.HTTP_401_UNAUTHORIZED:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                raise e
        return authorization


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=f"{settings.API_V1_STR}/auth/token")


def create_access_token(subject: str | Any, expires_delta: timedelta = None) -> str:
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


def decode_token(token: str) -> Optional[dict]:
    """
    Decodes a JWT token, trying multiple keys for rotation.
    """
    keys = [settings.SECRET_KEY] + settings.OLD_SECRET_KEYS
    for key in keys:
        try:
            payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            continue
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    """
    return pwd_context.hash(password)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    redis: Redis | None = Depends(get_redis_client),  # Allow None if Redis is disabled
) -> User:
    """
    Decode token and get current user.
    This function is a dependency that can be used to protect endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception
        token_data = TokenData(**payload)
        if token_data.jti is None:
            raise credentials_exception
    except (JWTError, ValidationError) as e:
        logger.warning(f"JWT decoding/validation failed: {e}")
        raise credentials_exception

    if redis:
        if redis_circuit_breaker.state == "OPEN":
            logger.error("Circuit is open for Redis. Failing fast.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is temporarily unavailable.",
            )

        try:
            start_time = time.time()
            if await redis.sismember("revoked_jti", token_data.jti):
                raise credentials_exception
            duration = time.time() - start_time
            logger.debug(f"Redis sismember check took {duration:.4f} seconds.")
            redis_circuit_breaker.record_success()
        except Exception as e:
            logger.error(f"Redis connection failed during token check: {e}")
            redis_circuit_breaker.record_failure()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is temporarily unavailable.",
            )

    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.sub)

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Any = Depends(get_current_user),
) -> Any:
    """
    Dependency to get the current user and verify they are active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def revoke_token(jti: str, redis: Redis | None):
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
