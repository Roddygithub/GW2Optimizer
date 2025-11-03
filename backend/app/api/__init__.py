"""
API Routes and Exports

This module serves as the main entry point for all API routes and exports
all the necessary components from submodules. It ensures that all routers
are properly registered with the FastAPI application.
"""

# Import all routers to ensure they're registered
from . import (  # noqa: F401
    ai,
    ai_optimizer,
    auth,
    builds,
    chat,
    export,
    health,
    learning,
    meta,
    scraper,
    teams,
    builds_db,
    teams_db,
    websocket_mcm,
    sentry_debug,
)

# Import individual routers for direct access
from .auth import router as auth_router  # noqa: F401
from .builds import router as builds_router  # noqa: F401
from .teams import router as teams_router  # noqa: F401
from .ai import router as ai_router  # noqa: F401
from .meta import router as meta_router  # noqa: F401
from .health import router as health_router  # noqa: F401

# Re-export commonly used components
__all__ = [
    # Module exports
    "ai",
    "ai_optimizer",
    "auth",
    "builds",
    "chat",
    "export",
    "health",
    "learning",
    "meta",
    "scraper",
    "teams",
    "builds_db",
    "teams_db",
    "websocket_mcm",
    "sentry_debug",
    # Router instances
    "auth_router",
    "builds_router",
    "teams_router",
    "ai_router",
    "meta_router",
    "health_router",
]
