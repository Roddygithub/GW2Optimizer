"""
Redis connection and utilities.
"""

import redis.asyncio as redis
from redis.asyncio import Redis  # noqa: F401 (used in type annotations)
from typing import Optional, Any

from app.core.config import settings
from app.core.logging import logger
from app.core.circuit_breaker import CircuitBreaker

redis_client: Optional[Any] = None
redis_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


async def get_redis_client() -> Optional[Any]:
    """
    Dependency to get the Redis client.
    """
    return redis_client


async def connect_to_redis() -> None:
    """Initializes the Redis client."""
    global redis_client
    if settings.REDIS_ENABLED:
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            retry_on_timeout=True,
        )
        await redis_client.ping()
        logger.info("✅ Connected to Redis successfully.")
    else:
        logger.warning("Redis is disabled. Token revocation will not be persistent.")
