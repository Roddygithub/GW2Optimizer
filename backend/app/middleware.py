"""Security and utility middleware for the FastAPI application.

This module defines middlewares for adding security headers, handling HTTPS redirection,
and adding correlation IDs and process time information to requests.
"""

import os
import time
import uuid
from typing import TYPE_CHECKING

from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.responses import Response

if TYPE_CHECKING:
    from app.core.config import Settings


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to add a X-Process-Time header to responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add a X-Request-ID correlation header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add essential security headers to all responses.
    This is a placeholder and should be configured with a strict policy for production.
    """

    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Relaxed CSP for development (allows Swagger/ReDoc CDN resources)
        if self.is_production:
            csp = "default-src 'self'; script-src 'self'; object-src 'none';"
        else:
            # Development: Allow CDN resources for Swagger UI and ReDoc
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "img-src 'self' data: https://fastapi.tiangolo.com https://render.guildwars2.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' https://api.guildwars2.com; "
                "object-src 'none';"
            )

        security_headers = {
            "Content-Security-Policy": csp,
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        if self.is_production:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class StripServerHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware that removes Server and X-Powered-By headers from responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header in ("server", "Server", "x-powered-by", "X-Powered-By"):
            if header in response.headers:
                del response.headers[header]
        return response


def add_security_middleware(app: FastAPI, settings: "Settings") -> None:
    """
    Adds all security-related middleware to the FastAPI app.

    Args:
        app: FastAPI application instance.
        settings: Application settings.
    """
    # Add Correlation ID and Process Time middlewares first
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(ProcessTimeMiddleware)

    # Redirect HTTP to HTTPS only when explicitly enabled and not under test
    is_testing = bool(getattr(settings, "TESTING", False)) or bool(os.getenv("PYTEST_CURRENT_TEST"))
    if settings.ENABLE_HTTPS_REDIRECT and not is_testing:
        app.add_middleware(HTTPSRedirectMiddleware)

    # Add custom security headers
    app.add_middleware(SecurityHeadersMiddleware, is_production=not settings.DEBUG)
