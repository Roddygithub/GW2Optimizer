"""Integration test for chat service circuit breaker."""

import pytest
import asyncio
import time
from datetime import datetime
from typing import List, Tuple

from app.core.circuit_breaker import CircuitBreaker
from app.models.chat import ChatRequest
from app.services.ai.chat_service import ChatService


@pytest.mark.asyncio
async def test_chat_service_circuit_breaker_sequence(caplog):
    """Ensure ChatService recovers after a transient Mistral outage."""

    class FakeMistralClient:
        def __init__(self):
            self.calls = 0

        async def chat(self, messages, temperature=0.7):  # pragma: no cover - simple stub
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("mistral down")
            return "Recovered response"

    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1, max_retries=0)
    service = ChatService(client=FakeMistralClient(), breaker=breaker)
    request = ChatRequest(message="Hello", version="1.0.0")

    caplog.set_level("INFO")

    states: List[Tuple[str, str, datetime]] = []

    states.append(("initial", breaker.state, datetime.utcnow()))

    start_first = time.perf_counter()
    response_fail = await service.process_message(request)
    end_first = time.perf_counter()
    states.append(("after_first", breaker.state, datetime.utcnow()))

    # Allow breaker to move from OPEN to HALF_OPEN
    await asyncio.sleep(0.11)
    states.append(("post_timeout", breaker.state, datetime.utcnow()))

    start_second = time.perf_counter()
    response_success = await service.process_message(request)
    end_second = time.perf_counter()
    states.append(("final", breaker.state, datetime.utcnow()))

    latencies = [end_first - start_first, end_second - start_second]

    assert "unavailable" in response_fail.response.lower()
    assert response_fail.metadata.get("circuit_state") == "OPEN"

    assert response_success.response == "Recovered response"
    assert response_success.metadata.get("error") is None

    assert states[0][1] == "CLOSED"
    assert states[1][1] == "OPEN"
    assert states[2][1] == "HALF_OPEN"
    assert states[3][1] == "CLOSED"

    log_messages = [record.message for record in caplog.records if "Circuit breaker" in record.message]
    assert any("opened" in msg for msg in log_messages)
    assert any("HALF_OPEN" in msg for msg in log_messages)
    assert any("reset" in msg for msg in log_messages)

    avg_latency = sum(latencies) / len(latencies)
    print(
        "QA Report:\n"
        f"States timeline: {states}\n"
        f"Latencies: {latencies}\n"
        f"Average latency: {avg_latency:.3f}s\n"
        f"Failure counter: {breaker._failures}\n"
    )
