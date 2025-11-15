"""
Custom Prometheus metrics for GW2Optimizer.

This module defines application-specific metrics beyond the default
HTTP metrics provided by prometheus-fastapi-instrumentator.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Optional

# ============================================================================
# AI & LLM Metrics
# ============================================================================

ai_requests_total = Counter(
    "gw2_ai_requests_total",
    "Total number of AI/LLM requests",
    ["model", "operation", "status"],
)

ai_request_duration = Histogram(
    "gw2_ai_request_duration_seconds",
    "AI/LLM request duration in seconds",
    ["model", "operation"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

ai_tokens_used = Counter(
    "gw2_ai_tokens_used_total",
    "Total number of tokens used by AI models",
    ["model", "token_type"],  # token_type: prompt, completion
)

ai_feedback_total = Counter(
    "gw2_ai_feedback_total",
    "Total AI feedback submissions",
    ["result"],  # result: ok, fallback, error
)

ai_training_triggers_total = Counter(
    "gw2_ai_training_triggers_total",
    "Total ML training triggers",
    ["result"],  # result: scheduled, disabled, error
)

# ============================================================================
# Database Metrics
# ============================================================================

db_query_duration = Histogram(
    "gw2_db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

db_connections_active = Gauge(
    "gw2_db_connections_active",
    "Number of active database connections",
)

db_errors_total = Counter(
    "gw2_db_errors_total",
    "Total database errors",
    ["operation", "error_type"],
)

# ============================================================================
# Cache Metrics
# ============================================================================

cache_operations_total = Counter(
    "gw2_cache_operations_total",
    "Total cache operations",
    ["operation", "result"],  # operation: get, set, delete; result: hit, miss, error
)

cache_hit_rate = Gauge(
    "gw2_cache_hit_rate",
    "Cache hit rate (0-1)",
)

cache_size_bytes = Gauge(
    "gw2_cache_size_bytes",
    "Current cache size in bytes",
)

# ============================================================================
# External API Metrics
# ============================================================================

external_api_requests_total = Counter(
    "gw2_external_api_requests_total",
    "Total external API requests",
    ["service", "endpoint", "status"],
)

external_api_duration = Histogram(
    "gw2_external_api_duration_seconds",
    "External API request duration in seconds",
    ["service", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# ============================================================================
# Business Metrics
# ============================================================================

builds_created_total = Counter(
    "gw2_builds_created_total",
    "Total builds created",
    ["profession", "game_mode"],
)

teams_created_total = Counter(
    "gw2_teams_created_total",
    "Total teams created",
    ["game_mode", "size"],
)

users_active = Gauge(
    "gw2_users_active",
    "Number of active users (last 24h)",
)

# ============================================================================
# Application Info
# ============================================================================

app_info = Info(
    "gw2_app",
    "GW2Optimizer application information",
)


# ============================================================================
# Helper Functions
# ============================================================================

def track_ai_request(
    model: str,
    operation: str,
    duration: float,
    status: str = "success",
    tokens_prompt: Optional[int] = None,
    tokens_completion: Optional[int] = None,
) -> None:
    """
    Track an AI/LLM request with all relevant metrics.
    
    Args:
        model: Model name (e.g., "mistral", "ollama")
        operation: Operation type (e.g., "compose_team", "optimize_build")
        duration: Request duration in seconds
        status: Request status (success, error, timeout)
        tokens_prompt: Number of prompt tokens used
        tokens_completion: Number of completion tokens used
    """
    ai_requests_total.labels(model=model, operation=operation, status=status).inc()
    ai_request_duration.labels(model=model, operation=operation).observe(duration)
    
    if tokens_prompt is not None:
        ai_tokens_used.labels(model=model, token_type="prompt").inc(tokens_prompt)
    if tokens_completion is not None:
        ai_tokens_used.labels(model=model, token_type="completion").inc(tokens_completion)


def track_db_query(operation: str, table: str, duration: float, error: Optional[str] = None) -> None:
    """
    Track a database query.
    
    Args:
        operation: Operation type (select, insert, update, delete)
        table: Table name
        duration: Query duration in seconds
        error: Error type if query failed
    """
    db_query_duration.labels(operation=operation, table=table).observe(duration)
    
    if error:
        db_errors_total.labels(operation=operation, error_type=error).inc()


def track_cache_operation(operation: str, result: str) -> None:
    """
    Track a cache operation.
    
    Args:
        operation: Operation type (get, set, delete)
        result: Operation result (hit, miss, error)
    """
    cache_operations_total.labels(operation=operation, result=result).inc()


def track_external_api(
    service: str,
    endpoint: str,
    duration: float,
    status: str = "success",
) -> None:
    """
    Track an external API request.
    
    Args:
        service: Service name (e.g., "gw2api", "wiki")
        endpoint: Endpoint path
        duration: Request duration in seconds
        status: HTTP status or error type
    """
    external_api_requests_total.labels(
        service=service,
        endpoint=endpoint,
        status=status,
    ).inc()
    external_api_duration.labels(service=service, endpoint=endpoint).observe(duration)


def initialize_app_info(version: str, environment: str) -> None:
    """
    Initialize application info metric.
    
    Args:
        version: Application version
        environment: Environment name (dev, staging, production)
    """
    app_info.info({
        "version": version,
        "environment": environment,
    })
