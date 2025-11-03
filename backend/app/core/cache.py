"""Cache management with Redis and disk fallback for GW2Optimizer."""

import json
import hashlib
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar  # noqa: F401 (used in type annotations)

import aiofiles

from app.core.config import settings
from app.core.logging import logger

# Type variable for generic functions
T = TypeVar("T")

# Initialize Redis client (optional dependency)
redis_client = None
try:
    import redis.asyncio as aioredis

    redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    logger.info("✅ Redis client initialized")
except ImportError:
    logger.warning("⚠️  Redis not installed, using disk cache fallback")
except Exception as e:
    logger.warning(f"⚠️  Could not connect to Redis: {e}, using disk cache fallback")

# Fallback disk cache directory
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class CacheManager:
    """
    Cache manager with Redis and disk fallback.

    Provides a unified interface for caching with automatic fallback
    to disk-based caching if Redis is unavailable.
    """

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value as string, or None if not found
        """
        try:
            # Try Redis first
            if redis_client:
                value = await redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return value

            # Fallback to disk cache
            cache_file = CACHE_DIR / f"{_hash_key(key)}.json"
            if cache_file.exists():
                async with aiofiles.open(cache_file, "r") as f:
                    content = await f.read()
                    logger.debug(f"Cache HIT (Disk): {key}")
                    return content

            logger.debug(f"Cache MISS: {key}")
            return None

        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    @staticmethod
    async def set(key: str, value: str, ttl: int = 3600) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (as string)
            ttl: Time to live in seconds (default: 1 hour)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try Redis first
            if redis_client:
                await redis_client.set(key, value, ex=ttl)
                logger.debug(f"Cache SET (Redis): {key} (TTL: {ttl}s)")
                return True

            # Fallback to disk cache
            cache_file = CACHE_DIR / f"{_hash_key(key)}.json"
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(value)
                logger.debug(f"Cache SET (Disk): {key}")
                return True

        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try Redis first
            if redis_client:
                await redis_client.delete(key)
                logger.debug(f"Cache DELETE (Redis): {key}")

            # Also delete from disk cache
            cache_file = CACHE_DIR / f"{_hash_key(key)}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Cache DELETE (Disk): {key}")

            return True

        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., "build:*")

        Returns:
            Number of keys deleted
        """
        try:
            count = 0

            # Try Redis first
            if redis_client:
                keys = await redis_client.keys(pattern)
                if keys:
                    count = await redis_client.delete(*keys)
                    logger.debug(f"Cache DELETE PATTERN (Redis): {pattern} ({count} keys)")

            # Also clean disk cache
            for cache_file in CACHE_DIR.glob("*.json"):
                # Simple pattern matching for disk cache
                if pattern.replace("*", "") in cache_file.stem:
                    cache_file.unlink()
                    count += 1

            return count

        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    @staticmethod
    async def clear() -> bool:
        """
        Clear all cache.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear Redis
            if redis_client:
                await redis_client.flushdb()
                logger.info("✅ Redis cache cleared")

            # Clear disk cache
            for cache_file in CACHE_DIR.glob("*.json"):
                cache_file.unlink()
            logger.info("✅ Disk cache cleared")

            return True

        except Exception as e:
            logger.error(f"❌ Error clearing cache: {e}")
            return False


def _hash_key(key: str) -> str:
    """
    Hash a cache key for safe filename usage.

    Args:
        key: Original cache key

    Returns:
        Hashed key suitable for filenames
    """
    return hashlib.sha256(key.encode()).hexdigest()


def cacheable(key_pattern: str, ttl: int = 3600):
    """
    Decorator to cache the result of an async function.

    Args:
        key_pattern: Cache key pattern (can use {arg_name} placeholders)
        ttl: Time to live in seconds (default: 1 hour)

    Example:
        @cacheable("build:{build_id}", ttl=3600)
        async def get_build(build_id: str):
            # ... expensive operation ...
            return build
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from pattern and kwargs
            try:
                cache_key = key_pattern.format(**kwargs)
            except KeyError:
                # If key pattern uses args, try to match them
                cache_key = key_pattern

            # Try to get from cache
            cached = await CacheManager.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    # If not JSON, return as is
                    return cached

            # Call the function if not in cache
            result = await func(*args, **kwargs)

            # Cache the result
            if result is not None:
                try:
                    cached_value = json.dumps(result) if not isinstance(result, str) else result
                    await CacheManager.set(cache_key, cached_value, ttl)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not cache result for {cache_key}: {e}")

            return result

        return wrapper

    return decorator


def invalidate_cache(*key_patterns: str):
    """
    Decorator to invalidate cache after function execution.

    Args:
        *key_patterns: Cache key patterns to invalidate

    Example:
        @invalidate_cache("build:{build_id}", "builds:user:{user_id}")
        async def update_build(build_id: str, user_id: str, data: dict):
            # ... update operation ...
            return updated_build
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Call the function first
            result = await func(*args, **kwargs)

            # Invalidate cache keys
            for pattern in key_patterns:
                try:
                    cache_key = pattern.format(**kwargs)
                    await CacheManager.delete(cache_key)
                except KeyError:
                    # If pattern uses wildcards, delete by pattern
                    if "*" in pattern:
                        await CacheManager.delete_pattern(pattern)

            return result

        return wrapper

    return decorator


# Convenience functions for common cache operations
async def cache_build(build_id: str, build_data: dict, ttl: int = 3600) -> bool:
    """Cache a build by ID."""
    return await CacheManager.set(f"build:{build_id}", json.dumps(build_data), ttl)


async def get_cached_build(build_id: str) -> Optional[dict]:
    """Get a cached build by ID."""
    cached = await CacheManager.get(f"build:{build_id}")
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            return None
    return None


async def invalidate_build_cache(build_id: str) -> bool:
    """Invalidate cache for a specific build."""
    return await CacheManager.delete(f"build:{build_id}")


async def cache_team(team_id: str, team_data: dict, ttl: int = 3600) -> bool:
    """Cache a team composition by ID."""
    return await CacheManager.set(f"team:{team_id}", json.dumps(team_data), ttl)


async def get_cached_team(team_id: str) -> Optional[dict]:
    """Get a cached team composition by ID."""
    cached = await CacheManager.get(f"team:{team_id}")
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            return None
    return None


async def invalidate_team_cache(team_id: str) -> bool:
    """Invalidate cache for a specific team."""
    return await CacheManager.delete(f"team:{team_id}")
