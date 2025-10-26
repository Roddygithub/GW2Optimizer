"""Unit tests for circuit breaker implementation."""

import asyncio
import logging
import time
import pytest
from unittest.mock import AsyncMock, patch

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError, chat_service_circuit_breaker

# Set up test logger
logger = logging.getLogger(__name__)


# Mock function for testing
async def mock_success():
    return "success"


async def mock_failure():
    raise Exception("Simulated failure")


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""

    @pytest.fixture
    def circuit(self):
        """Create a fresh circuit breaker for each test."""
        return CircuitBreaker(failure_threshold=2, recovery_timeout=1, max_retries=1)

    @pytest.mark.asyncio
    async def test_closed_state_success(self, circuit):
        """Test successful call in CLOSED state."""
        result = await circuit.call_async(mock_success)
        assert result == "success"
        assert circuit.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_closed_to_open_transition(self, circuit):
        """Test transition from CLOSED to OPEN on failures."""
        # Should start in CLOSED state
        assert circuit.state == "CLOSED"

        # First failure
        with pytest.raises(Exception):
            await circuit.call_async(mock_failure)
        assert circuit.state == "CLOSED"

        # Second failure should open the circuit (failure_threshold=2)
        with pytest.raises(Exception):
            await circuit.call_async(mock_failure)

        # Now the circuit should be OPEN
        assert circuit.state == "OPEN"

        # Next call should fail fast with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await circuit.call_async(mock_success)

    @pytest.mark.asyncio
    async def test_open_to_half_open_transition(self, circuit):
        """Test transition from OPEN to HALF_OPEN after recovery timeout."""
        # Trigger OPEN state
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit.call_async(mock_failure)

        # Fast-forward time to trigger HALF_OPEN
        with patch("time.time", return_value=time.time() + 2):
            assert circuit.state == "HALF_OPEN"

    @pytest.mark.asyncio
    async def test_half_open_to_closed(self, circuit):
        """Test successful recovery from HALF_OPEN to CLOSED."""
        # Trigger OPEN state with failures
        for _ in range(2):
            with pytest.raises(Exception):
                await circuit.call_async(mock_failure)

        assert circuit.state == "OPEN"

        # Fast-forward past recovery timeout
        with patch("time.time", return_value=time.time() + 2):
            # The circuit should now be HALF_OPEN
            assert circuit.state == "HALF_OPEN"

            # Mock a successful call
            with patch("asyncio.sleep"):  # Mock sleep to speed up the test
                # First call in HALF_OPEN state should be allowed
                result = await circuit.call_async(mock_success)
                assert result == "success"
                # After a successful call, circuit should be CLOSED
                assert circuit.state == "CLOSED"

                # Verify subsequent calls work normally
                result = await circuit.call_async(mock_success)
                assert result == "success"
                assert circuit.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, circuit):
        """Test the retry mechanism with backoff.

        Verifies that:
        - The function is retried when it fails
        - The circuit remains CLOSED after successful retry
        - The failure counter is reset after success
        - The backoff delay is calculated correctly
        """
        # Create a new circuit breaker with max_retries=1 for this test
        circuit = CircuitBreaker(
            failure_threshold=3,  # Need to fail 3 times to open the circuit
            recovery_timeout=1,
            max_retries=1,  # Will retry once (total of 2 attempts)
        )

        # Reset the circuit to ensure clean state
        circuit.reset()
        assert circuit.state == "CLOSED"
        assert circuit._failures == 0

        # Track function calls
        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                raise Exception("Temporary failure")
            # Second call succeeds
            return "success"

        # Mock sleep to avoid waiting in tests
        with patch("asyncio.sleep") as mock_sleep, patch("logging.Logger.warning") as mock_warning:

            # The circuit breaker should retry once (total of 2 attempts)
            result = await circuit.call_async(mock_func)

            # Verify sleep was called with the correct backoff (2^1 = 2 seconds)
            mock_sleep.assert_called_once_with(2)

            # Verify warning logging captured the failure message
            assert any("Attempt 1 failed" in str(call) for call in mock_warning.call_args_list)

        # Verify function was called twice (initial + 1 retry)
        assert call_count == 2, "Function should have been called twice (initial + 1 retry)"

        # Verify the result is as expected
        assert result == "success", "Should return success on second attempt"

        # Verify circuit breaker state is reset after success
        assert circuit.state == "CLOSED", "Circuit should be CLOSED after successful call"
        assert circuit._failures == 0, "Failure count should be reset after success"
        assert circuit._state == "CLOSED", "Circuit state should be CLOSED"

    @pytest.mark.asyncio
    async def test_execute_blocks_when_recently_open(self, circuit):
        """Ensure calls fail fast when the circuit was recently opened."""
        circuit._state = "OPEN"
        circuit._last_failure_time = time.time()

        with pytest.raises(CircuitBreakerError):
            await circuit._execute_with_retry(mock_success)

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, circuit):
        """Failing probe in HALF_OPEN should reopen the circuit immediately."""
        circuit._state = "HALF_OPEN"
        circuit._last_failure_time = time.time() - circuit.recovery_timeout - 1

        async def failing_call():
            raise RuntimeError("still failing")

        with pytest.raises(CircuitBreakerError):
            await circuit._execute_with_retry(failing_call)

        assert circuit.state == "OPEN"

    def test_record_failure_does_not_increment_when_open(self, circuit):
        """Recording failure while already OPEN should not change the counter."""
        circuit._state = "OPEN"
        circuit._failures = 3

        circuit._record_failure()

        assert circuit._failures == 3

    def test_record_success_resets_state_and_counter(self, circuit):
        """Successful call should reset state and failure counter."""
        circuit._state = "HALF_OPEN"
        circuit._failures = 2

        circuit._record_success()

        assert circuit.state == "CLOSED"
        assert circuit._failures == 0

    @pytest.mark.asyncio
    async def test_retry_exhaustion_raises_original_exception(self):
        """When threshold is not reached, propagate the last exception."""
        circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=1, max_retries=0)

        async def failing_call():
            raise ValueError("boom")

        with pytest.raises(ValueError):
            await circuit._execute_with_retry(failing_call)

        assert circuit.state == "CLOSED"
        assert circuit._failures == 1

    @pytest.mark.asyncio
    async def test_timeout_handling(self, circuit):
        """Test timeout handling in circuit breaker."""

        async def slow_func():
            await asyncio.sleep(2)
            return "slow"

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(circuit.call_async(slow_func), timeout=0.1)


def test_circuit_breaker_decorator():
    """Test the circuit_breaker decorator."""
    from app.core.circuit_breaker import circuit_breaker, CircuitBreakerError

    # Create a new circuit breaker for testing
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

    # Test successful call
    @circuit_breaker(cb)
    async def test_success():
        return "test"

    # Test failing call
    @circuit_breaker(cb)
    async def test_failure():
        raise Exception("Test failure")

    # Should work normally first time
    assert asyncio.run(test_success()) == "test"

    # Should fail and open the circuit
    with pytest.raises(Exception):
        asyncio.run(test_failure())

    # Next call should raise CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        asyncio.run(test_success())
