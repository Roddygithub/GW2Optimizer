"""Security middleware for adding security headers and handling HTTPS redirection."""
import os
import time
import uuid
from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.responses import Response


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to add a X-Process-Time header."""
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add a X-Request-ID correlation header."""
    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.correlation_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Implements:
    - Content Security Policy (CSP)
    - HTTP Strict Transport Security (HSTS)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """
    
    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers configuration
        security_headers: Dict[str, str] = { # type: ignore
            # Content Security Policy
            "Content-Security-Policy": self._get_csp_header(),
            
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS filtering
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        # Add HSTS header in production only
        if self.is_production:
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload" # type: ignore
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
            
        # Remove Server header in production for obscurity
        if self.is_production and "server" in response.headers:
            del response.headers["server"]
            
        return response
    
    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header."""
        csp_directives = [
            # Default policy
            "default-src 'self'", # Restricts all resources to the same origin.
            
            # Script sources
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net", # Allows scripts from self, inline scripts, and jsdelivr CDN.
            
            # Style sources
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net", # Allows styles from self, inline styles, and jsdelivr CDN.
            
            # Image sources
            "img-src 'self' data: https:", # Allows images from self, data URIs, and any HTTPS source.
            
            # Font sources
            "font-src 'self' data:", # Allows fonts from self and data URIs.
            
            # Connect sources
            "connect-src 'self'", # Restricts AJAX, WebSockets, etc., to the same origin.
            
            # Media sources
            "media-src 'self'", # Restricts audio and video to the same origin.
            
            # Object sources
            "object-src 'none'", # Disallows <object>, <embed>, and <applet> elements.
            
            # Form actions
            "form-action 'self'", # Restricts where forms can be submitted to.
            
            # Frame ancestors
            "frame-ancestors 'none'", # Prevents the page from being embedded in iframes (clickjacking protection).
            
            # Base URI
            "base-uri 'self'", # Restricts the URLs that can be used in a document's <base> element.
            
            # Upgrade insecure requests (enabled in production)
            "upgrade-insecure-requests" if self.is_production else "" # Instructs browsers to upgrade HTTP requests to HTTPS.
        ]
        
        return "; ".join(filter(None, csp_directives))


def add_security_middleware(app, settings):
    """
    Add all security-related middleware to the FastAPI app.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Add Correlation ID and Process Time middlewares
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(ProcessTimeMiddleware)

    # Redirect HTTP to HTTPS in production
    is_testing = bool(getattr(settings, "TESTING", False)) or bool(os.getenv("PYTEST_CURRENT_TEST"))
    if settings.ENABLE_HTTPS_REDIRECT and not is_testing:
        app.add_middleware(HTTPSRedirectMiddleware)

    # Add custom security headers
    app.add_middleware(
        SecurityHeadersMiddleware,
        is_production=not settings.DEBUG
    )