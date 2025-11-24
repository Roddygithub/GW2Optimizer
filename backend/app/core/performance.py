"""
Performance optimization utilities.
Lazy loading, caching, async batching, etc.
"""

import asyncio
from functools import wraps, lru_cache
from typing import Any, Callable, Coroutine, TypeVar, ParamSpec
from contextlib import asynccontextmanager
import time

from app.core.logging import logger


P = ParamSpec("P")
T = TypeVar("T")


def timed(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to measure function execution time.
    
    Usage:
        @timed
        def slow_function():
            ...
    """
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(
            f"⏱️ {func.__name__} took {elapsed:.3f}s",
            extra={"function": func.__name__, "duration_ms": elapsed * 1000}
        )
        return result
    return wrapper


def async_timed(func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    Decorator to measure async function execution time.
    
    Usage:
        @async_timed
        async def slow_async_function():
            ...
    """
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(
            f"⏱️ {func.__name__} took {elapsed:.3f}s",
            extra={"function": func.__name__, "duration_ms": elapsed * 1000}
        )
        return result
    return wrapper


class AsyncBatchProcessor:
    """
    Batch process async operations for better performance.
    
    Usage:
        processor = AsyncBatchProcessor()
        results = await processor.batch_process([item1, item2, ...], process_func)
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(
        self,
        item: Any,
        func: Callable[[Any], Coroutine[Any, Any, T]]
    ) -> T:
        """Process a single item with concurrency limit."""
        async with self.semaphore:
            return await func(item)
    
    async def batch_process(
        self,
        items: list[Any],
        func: Callable[[Any], Coroutine[Any, Any, T]],
        show_progress: bool = False
    ) -> list[T]:
        """
        Process multiple items concurrently with a limit.
        
        Args:
            items: List of items to process
            func: Async function to apply to each item
            show_progress: Whether to log progress
        
        Returns:
            List of results
        """
        tasks = [self.process_with_limit(item, func) for item in items]
        
        if show_progress:
            logger.info(f"🔄 Processing {len(items)} items (max {self.max_concurrent} concurrent)")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = len(results) - successes
        
        if show_progress:
            logger.info(f"✅ Processed {successes}/{len(items)} items ({failures} failures)")
        
        return results


@asynccontextmanager
async def async_timer(name: str = "Operation"):
    """
    Context manager to time async operations.
    
    Usage:
        async with async_timer("Database query"):
            result = await db.query(...)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.debug(
            f"⏱️ {name} completed in {elapsed:.3f}s",
            extra={"operation": name, "duration_ms": elapsed * 1000}
        )


# Cache decorator with TTL
def cached_with_ttl(ttl_seconds: int = 300):
    """
    LRU cache with Time-To-Live.
    
    Args:
        ttl_seconds: Cache validity in seconds (default 5 minutes)
    
    Usage:
        @cached_with_ttl(ttl_seconds=60)
        def expensive_computation(x):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        cache: dict[tuple, tuple[float, T]] = {}
        
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Create cache key
            key = (args, tuple(sorted(kwargs.items())))
            
            # Check cache
            if key in cache:
                timestamp, value = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    logger.debug(f"🎯 Cache hit for {func.__name__}")
                    return value
                else:
                    logger.debug(f"⏰ Cache expired for {func.__name__}")
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache[key] = (time.time(), result)
            logger.debug(f"💾 Cached result for {func.__name__}")
            
            return result
        
        # Add cache clearing method
        wrapper.clear_cache = lambda: cache.clear()  # type: ignore
        
        return wrapper
    return decorator


# Lazy loading helper
class LazyLoader:
    """
    Lazy load heavy imports only when needed.
    
    Usage:
        matplotlib = LazyLoader("matplotlib")
        # matplotlib is only imported when first accessed
        plt = matplotlib.pyplot
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, item: str) -> Any:
        if self._module is None:
            logger.debug(f"⚡ Lazy loading {self.module_name}")
            import importlib
            self._module = importlib.import_module(self.module_name)
        return getattr(self._module, item)


# Global batch processor instance
batch_processor = AsyncBatchProcessor(max_concurrent=10)


__all__ = [
    "timed",
    "async_timed",
    "AsyncBatchProcessor",
    "async_timer",
    "cached_with_ttl",
    "LazyLoader",
    "batch_processor",
]
