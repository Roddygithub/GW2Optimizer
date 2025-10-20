"""
Redis connection and utilities.
"""

import redis.asyncio as redis
from redis.asyncio import Redis
from typing import AsyncGenerator, Optional

from app.core.config import settings
from app.core.logging import logger
from app.core.circuit_breaker import CircuitBreaker

redis_client: Optional[Redis] = None
redis_circuit_breaker = CircuitBreaker(max_failures=5, reset_timeout=60)


async def get_redis_client() -> Optional[Redis]:
    """
    Dependency to get the Redis client.
    """
    return redis_client


async def connect_to_redis():
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
