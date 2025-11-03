"""Core application configuration and utilities.

This module contains core functionality used throughout the application,
including configuration, logging, caching, and circuit breaking.
"""

from .config import settings  # noqa: F401
from .logging import logger  # noqa: F401
from .cache import CacheManager, cacheable, invalidate_cache  # noqa: F401
from .circuit_breaker import CircuitBreaker, CircuitBreakerError  # noqa: F401
from .redis import get_redis_client, connect_to_redis  # noqa: F401

__all__ = [
    'settings',
    'logger',
    'CacheManager',
    'cacheable',
    'invalidate_cache',
    'CircuitBreaker',
    'CircuitBreakerError',
    'get_redis_client',
    'connect_to_redis',
]
