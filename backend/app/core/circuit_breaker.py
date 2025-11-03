"""
Circuit Breaker implementation for handling failures in distributed systems.
"""

import time
import asyncio
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, TypeVar  # noqa: F401 (used in type annotations)

from app.core.logging import logger

# Type variable for generic function typing
T = TypeVar("T")


class CircuitBreakerError(Exception):
    """Exception raised when the circuit breaker is open."""

    def __init__(self, circuit_breaker: "CircuitBreaker", message: str = None):
        self.circuit_breaker = circuit_breaker
        self.message = message or f"Circuit breaker is {circuit_breaker.state}"
        super().__init__(self.message)


class CircuitBreaker:
    """Resiliency primitive that guards async calls against repeated failures.

    States
    -------
    * ``CLOSED`` – normal operation; failures are counted toward the threshold.
    * ``OPEN`` – all calls fail fast until ``recovery_timeout`` elapses.
    * ``HALF_OPEN`` – a single probe call is allowed after the open timeout; success
      closes the breaker, failure sends it back to ``OPEN`` immediately.

    Transitions
    -----------
    * ``CLOSED`` → ``OPEN`` when recorded failures reach ``failure_threshold``.
    * ``OPEN`` → ``HALF_OPEN`` once ``recovery_timeout`` seconds have passed since the
      last failure.
    * ``HALF_OPEN`` → ``CLOSED`` on a successful probe; otherwise ``HALF_OPEN`` →
      ``OPEN`` on the first failure.

    Retry & Backoff
    ----------------
    Each call can retry up to ``max_retries`` times. Attempts use exponential backoff
    (``min(2**attempt, 10)`` seconds) between retries. Failures only contribute to the
    breaker threshold when all retries for a call are exhausted. Successful calls reset
    the failure counter to zero.

    Example
    -------
    >>> @circuit_breaker()
    ... async def fetch_profile(user_id: str) -> dict:
    ...     return await external_service.get(user_id)

    Args:
        failure_threshold: Number of consecutive failed calls before opening the circuit.
        recovery_timeout: Seconds to wait before allowing a HALF_OPEN probe.
        max_retries: Retry attempts (in addition to the initial call) for each invocation.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, max_retries: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.max_retries = max_retries
        self._failures = 0
        self._state = "CLOSED"
        self._last_failure_time = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        """Get the current state of the circuit breaker."""
        # Only transition from OPEN to HALF_OPEN if enough time has passed
        if self._state == "OPEN" and (time.time() - self._last_failure_time) > self.recovery_timeout:
            self._state = "HALF_OPEN"
            logger.info("Circuit breaker moved to HALF_OPEN state")
        return self._state

    async def call_async(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """
        Call an async function with circuit breaker logic.

        Args:
            func: The async function to call
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function call

        Raises:
            CircuitBreakerError: If the circuit is open
            Exception: Any exception raised by the function
        """
        # Check circuit state before proceeding
        if self.state == "OPEN":
            raise CircuitBreakerError(self, "Circuit breaker is open")

        # If we're in HALF_OPEN state, only allow one request through
        if self.state == "HALF_OPEN" and not self._lock.locked():
            async with self._lock:
                return await self._execute_with_retry(func, *args, **kwargs)

        # Normal operation in CLOSED state
        return await self._execute_with_retry(func, *args, **kwargs)

    async def _execute_with_retry(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """Execute the function with retry logic."""
        last_exception = None

        # Check circuit state before attempting to execute
        if self.state == "OPEN":
            # Check if we should transition to HALF_OPEN
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "HALF_OPEN"
                logger.info("Circuit breaker is HALF_OPEN, allowing a test call")
            else:
                raise CircuitBreakerError(self, "Circuit breaker is open")

        # Total attempts = 1 (initial) + max_retries
        for attempt in range(1, self.max_retries + 2):
            try:
                logger.debug(f"Attempt {attempt}/{self.max_retries + 1} - Calling function")
                result = await func(*args, **kwargs)
                logger.debug(f"Attempt {attempt} succeeded with result: {result}")

                # Reset failures on success
                self._failures = 0
                # Only transition to CLOSED if we were in HALF_OPEN
                if self._state == "HALF_OPEN":
                    self._state = "CLOSED"
                    logger.info("Circuit breaker reset to CLOSED after successful test call")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {str(e)}")

                if self._state == "HALF_OPEN":
                    self._state = "OPEN"
                    self._last_failure_time = time.time()
                    logger.error("Test call in HALF_OPEN state failed, reopening circuit")
                    raise CircuitBreakerError(self, "Circuit breaker is open") from e

                has_retry = attempt <= self.max_retries
                if has_retry:
                    retry_delay = min(2**attempt, 10)  # Exponential backoff, max 10s
                    logger.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    continue

                # No retries left – record the failure for this overall call
                self._record_failure()
                if self._state == "OPEN":
                    raise CircuitBreakerError(self, "Circuit breaker is open") from e
                raise last_exception or Exception("Unknown error in circuit breaker")

        # All attempts succeeded and returned earlier
        raise last_exception or Exception("Unknown error in circuit breaker")

    def _record_failure(self) -> None:
        """Record a failed call."""
        # Always update the last failure time
        self._last_failure_time = time.time()

        # If we're already OPEN, don't record additional failures
        if self._state == "OPEN":
            return

        # Increment failure count
        self._failures += 1
        logger.warning(f"Circuit breaker failure recorded. Total failures: {self._failures}")

        # Check if we've hit the failure threshold
        if self._failures >= self.failure_threshold:
            self._state = "OPEN"
            logger.error(
                f"Circuit breaker opened after {self._failures} failures. Will retry in {self.recovery_timeout} seconds"
            )

    def _record_success(self) -> None:
        """Record a successful call and reset the circuit if needed."""
        if self._state != "CLOSED":
            logger.info("Circuit breaker reset after successful call")
            self._state = "CLOSED"
        self._failures = 0

    # --- Public helpers expected by tests (wrappers) ---
    def record_failure(self) -> None:
        """Public wrapper to record a failure (used by tests)."""
        self._record_failure()

    def record_success(self) -> None:
        """Public wrapper to record a success (used by tests)."""
        self._record_success()

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = "CLOSED"
        self._failures = 0
        self._last_failure_time = 0.0
        logger.info("Circuit breaker manually reset")


# Global circuit breaker instance for chat service
chat_service_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60, max_retries=3)


# Decorator for async functions
def circuit_breaker(breaker: Optional[CircuitBreaker] = None):
    """Decorator factory applying circuit breaker protection to async callables."""

    def decorator(func: Callable[..., Awaitable[T]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            selected = breaker
            if selected is None:
                # Attempt to use an injected breaker from the bound instance.
                if args:
                    instance = args[0]
                    selected = getattr(instance, "breaker", None)
            selected = selected or chat_service_circuit_breaker
            return await selected.call_async(func, *args, **kwargs)

        return wrapper

    return decorator
