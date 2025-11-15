"""
Performance monitoring middleware.

Tracks request/response times and logs slow requests.
"""

import time
from typing import Any, Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request performance.
    
    - Adds X-Response-Time header to all responses
    - Logs slow requests (>1s by default)
    - Can be used with Prometheus metrics
    """
    
    def __init__(self, app: ASGIApp, slow_threshold: float = 1.0) -> None:
        """
        Initialize performance middleware.
        
        Args:
            app: FastAPI application
            slow_threshold: Threshold in seconds for slow request logging
        """
        super().__init__(app)
        self.slow_threshold = slow_threshold
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Any]]
    ) -> Any:
        """Process request and track performance."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # Note: HTTP metrics are already tracked by prometheus-fastapi-instrumentator
        # Custom metrics can be added here if needed
        
        # Log slow requests
        if duration > self.slow_threshold:
            logger.warning(
                "Slow request detected",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_seconds": duration,
                    "status_code": response.status_code,
                },
            )
        
        return response
