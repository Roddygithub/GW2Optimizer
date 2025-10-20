"""
A simple asynchronous Circuit Breaker implementation.
"""

import time
from functools import wraps
from typing import Any, Callable, Coroutine

from app.core.logging import logger


class CircuitBreaker:
    """
    A simple implementation of the Circuit Breaker pattern to prevent
    cascading failures when a service is down.
    """

    def __init__(self, max_failures: int = 3, reset_timeout: int = 60):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._state = "CLOSED"  # Can be CLOSED, OPEN, HALF_OPEN
        self._last_failure_time = 0

    @property
    def state(self) -> str:
        """Check if the circuit should be moved to HALF_OPEN state."""
        if self._state == "OPEN" and (time.time() - self._last_failure_time) > self.reset_timeout:
            self._state = "HALF_OPEN"
            logger.info("Circuit Breaker is now HALF_OPEN.")
        return self._state

    def record_failure(self) -> None:
        """Record a failure and open the circuit if the threshold is reached."""
        self._failures += 1
        if self._failures >= self.max_failures:
            self._state = "OPEN"
            self._last_failure_time = time.time()
            logger.error(f"Circuit Breaker is now OPEN for {self.reset_timeout}s due to {self._failures} failures.")

    def record_success(self) -> None:
        """Reset the circuit on success."""
        if self._state != "CLOSED":
            logger.info("Circuit Breaker is now CLOSED.")
        self._failures = 0
        self._state = "CLOSED"


# Global instance for Redis operations
redis_circuit_breaker = CircuitBreaker()
