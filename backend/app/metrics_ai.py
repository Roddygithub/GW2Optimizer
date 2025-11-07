"""Prometheus metrics helpers for AI feedback orchestration.

The module avoids hard dependencies on ``prometheus_client``. If the library
is unavailable the counters gracefully degrade to ``None`` and callers must
check before using them.
"""

from __future__ import annotations

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter
except Exception:  # pragma: no cover - prom may be absent
    Counter = None  # type: ignore[assignment]


if Counter is not None:  # pragma: no branch - simple guards
    feedback_total = Counter(
        "ai_feedback_total",
        "AI feedback submissions",
        labelnames=("result",),
    )
    training_triggers_total = Counter(
        "ai_training_triggers_total",
        "Background trainer trigger attempts",
        labelnames=("result",),
    )
else:  # pragma: no cover - when prometheus_client missing
    feedback_total = None  # type: ignore[assignment]
    training_triggers_total = None  # type: ignore[assignment]


__all__ = ["feedback_total", "training_triggers_total"]
