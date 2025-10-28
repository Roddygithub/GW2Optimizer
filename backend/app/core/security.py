from datetime import datetime, timedelta
from typing import Any, Optional, Set
import uuid
import time

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from pydantic import ValidationError

from app.core.config import settings
from app.db.session import get_db

# JWT Algorithm
ALGORITHM = "HS256"
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
oauth2_optional_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)


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
    redis: Redis | None,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    print(f"[DEBUG] _resolve_user_from_token - Starting token validation")
    
    try:
        print(f"[DEBUG] _resolve_user_from_token - Decoding token")
        payload = decode_token(token)
        print(f"[DEBUG] _resolve_user_from_token - Decoded payload: {payload}")
        
        if payload is None:
            print("[DEBUG] _resolve_user_from_token - Payload is None")
            raise credentials_exception
            
        token_data = TokenData(**payload)
        print(f"[DEBUG] _resolve_user_from_token - Token data: {token_data}")
        
        if token_data.jti is None:
            print("[DEBUG] _resolve_user_from_token - JTI is None")
            raise credentials_exception
            
    except (JWTError, ValidationError) as e:
        logger.warning(f"JWT decoding/validation failed: {e}")
        print(f"[DEBUG] _resolve_user_from_token - JWT validation error: {e}")
        raise credentials_exception from e

    token_revoked_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token revoked or expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if redis is not None:
        print(f"[DEBUG] _resolve_user_from_token - Redis client is available")
        print(f"[DEBUG] _resolve_user_from_token - Redis client type: {type(redis).__name__}")
        print(f"[DEBUG] _resolve_user_from_token - Circuit breaker state: {redis_circuit_breaker.state}")

        if redis_circuit_breaker.state != "OPEN":
            try:
                print(f"[DEBUG] _resolve_user_from_token - Checking Redis for revoked token with JTI: {token_data.jti}")

                revoked_jtis = await redis.smembers("revoked_jti")
                print(f"[DEBUG] _resolve_user_from_token - Raw revoked JTIs from Redis: {revoked_jtis}")

                revoked_jtis_set = set()
                for j in revoked_jtis:
                    if isinstance(j, bytes):
                        try:
                            j = j.decode("utf-8")
                        except UnicodeDecodeError:
                            print(f"[DEBUG] _resolve_user_from_token - Error decoding JTI: {j}")
                            continue
                    revoked_jtis_set.add(j)

                print(f"[DEBUG] _resolve_user_from_token - Decoded revoked JTIs: {revoked_jtis_set}")
                print(f"[DEBUG] _resolve_user_from_token - Token JTI to check: {token_data.jti} (type: {type(token_data.jti)})")

                if token_data.jti in revoked_jtis_set:
                    print("[DEBUG] _resolve_user_from_token - Token is revoked, raising explicit exception")
                    raise token_revoked_exc

                print("[DEBUG] _resolve_user_from_token - Token is not revoked, continuing...")
                redis_circuit_breaker.record_success()

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Redis connection failed during token check: {e}", exc_info=True)
                print(f"[DEBUG] _resolve_user_from_token - Redis error: {e}")
                import traceback
                print(f"[DEBUG] _resolve_user_from_token - Traceback: {traceback.format_exc()}")
                redis_circuit_breaker.record_failure()

                if redis_circuit_breaker.state == "OPEN":
                    logger.warning("Circuit breaker is OPEN, continuing without token revocation check")
                else:
                    logger.warning("Unexpected Redis error, continuing without token revocation check")
        else:
            print("[DEBUG] _resolve_user_from_token - Circuit breaker is OPEN, skipping Redis check")
    else:
        print("[DEBUG] _resolve_user_from_token - Redis client is None, skipping revocation check")

    print(f"[DEBUG] _resolve_user_from_token - Getting user from database with ID: {token_data.sub}")
    
    user_service = UserService(db)
    user = await user_service.get_by_id(token_data.sub)
    
    if user is None:
        print("[DEBUG] _resolve_user_from_token - User not found in database")
        raise credentials_exception
        
    print(f"[DEBUG] _resolve_user_from_token - Found user: {user.id}, is_superuser: {getattr(user, 'is_superuser', 'N/A')}")
    return user


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    redis: Redis | None = Depends(get_redis_client),  # Allow None if Redis is disabled
) -> User:
    """Decode token and return the authenticated user."""
    # Debug: Print the received token
    print(f"[DEBUG] get_current_user - Received token: {token}")
    
    try:
        user = await _resolve_user_from_token(token, db, redis)
        print(f"[DEBUG] get_current_user - Authenticated user: {user.id}, is_superuser: {getattr(user, 'is_superuser', 'N/A')}")
        return user
    except Exception as e:
        print(f"[DEBUG] get_current_user - Error: {str(e)}")
        raise


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: str | None = Depends(oauth2_optional_scheme),
    redis: Redis | None = Depends(get_redis_client),
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


async def revoke_token(jti: str, redis: Redis | None):
    """
    Adds a token's JTI to the revocation list in Redis with an expiration
    time matching the access token's lifetime.
    """
    print(f"[DEBUG] revoke_token - Starting revocation for JTI: {jti}")
    
    if not redis:
        msg = "Redis is not available. Token revocation is not being performed."
        logger.warning(msg)
        print(f"[DEBUG] {msg}")
        return

    if redis_circuit_breaker.state == "OPEN":
        msg = f"Circuit is open. Skipping token revocation for JTI {jti}."
        logger.error(msg)
        print(f"[DEBUG] {msg}")
        return

    try:
        print(f"[DEBUG] revoke_token - Adding JTI {jti} to revoked_jti set")
        
        # Check current state before making changes
        is_already_revoked = await redis.sismember("revoked_jti", jti)
        print(f"[DEBUG] revoke_token - Is JTI {jti} already revoked? {is_already_revoked}")
        
        # Get current TTL for debugging
        try:
            ttl = await redis.ttl("revoked_jti")
            print(f"[DEBUG] revoke_token - Current TTL for revoked_jti: {ttl} seconds")
        except Exception as e:
            print(f"[DEBUG] revoke_token - Could not get TTL for revoked_jti: {e}")
        
        start_time = time.time()
        async with redis.pipeline(transaction=True) as pipe:
            # Add the JTI to the revoked set
            await pipe.sadd("revoked_jti", jti)
            # The expiration should be slightly longer than the token's lifetime to be safe.
            expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 5
            print(f"[DEBUG] revoke_token - Setting TTL for revoked_jti to {expire_seconds} seconds")
            await pipe.expire("revoked_jti", expire_seconds)
            
            # Execute the pipeline
            results = await pipe.execute()
            print(f"[DEBUG] revoke_token - Pipeline results: {results}")
            
        duration = time.time() - start_time
        logger.info(f"Token revocation for JTI {jti} took {duration:.4f} seconds.")
        print(f"[DEBUG] revoke_token - Successfully revoked token JTI {jti}")
        
        # Verify the JTI was added
        is_now_revoked = await redis.sismember("revoked_jti", jti)
        print(f"[DEBUG] revoke_token - Verification: Is JTI {jti} now in revoked set? {is_now_revoked}")
        
        # Get all revoked JTIs for debugging
        revoked_jtis = await redis.smembers("revoked_jti")
        print(f"[DEBUG] revoke_token - Current revoked JTIs: {revoked_jtis}")
        
        redis_circuit_breaker.record_success()
        return True
        
    except Exception as e:
        error_msg = f"Failed to revoke token JTI {jti} in Redis: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"[DEBUG] {error_msg}")
        redis_circuit_breaker.record_failure()
        return False
