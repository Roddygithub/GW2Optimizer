"""
Main FastAPI application module.

This module initializes the FastAPI application, configures middleware,
and includes all API routers.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List, Optional

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import logger
from app.middleware import add_security_middleware
from app.core.redis import connect_to_redis, redis_client
from app.exceptions import add_exception_handlers
from app.api import (
    ai,
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
)
from app.api.auth import limiter as auth_limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting GW2Optimizer Backend")
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🌍 API Version: {settings.API_VERSION}")
    logger.info(f"🔗 API Base URL: {settings.API_V1_STR}")
    logger.info(f"🔌 Ollama Host: {settings.OLLAMA_HOST}")

    # Initialize database
    try:
        from app.db.init_db import init_db

        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

    # Initialize Redis
    try:
        await connect_to_redis()
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        # Depending on requirements, you might want to raise here

    # Start background tasks
    try:
        from app.services.scheduler import scheduler

        scheduler.start()
        logger.info("⏰ Learning pipeline scheduler activated")
    except Exception as e:
        logger.warning(f"⚠️ Failed to start scheduler: {str(e)}")

    yield

    # Shutdown
    logger.info("🛑 Shutting down GW2Optimizer Backend")
    try:
        from app.services.scheduler import scheduler

        scheduler.shutdown()
    except Exception as e:
        logger.error(f"❌ Error shutting down scheduler: {str(e)}")

    # Close Redis connection
    if settings.REDIS_ENABLED and redis_client:
        await redis_client.close()
        logger.info("🔌 Redis connection closed.")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="GW2Optimizer API",
        description="API for GW2Optimizer - Optimize your Guild Wars 2 gameplay",
        version=settings.API_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Add rate limiting (disabled in testing mode)
    if not settings.TESTING:
        app.state.limiter = auth_limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    else:
        # Disable rate limiting in tests
        logger.info("⚠️  Rate limiting DISABLED (TESTING=True)")

    # Configure CORS
    configure_cors(app)

    # Add security middleware
    add_security_middleware(app, settings)

    # Add exception handlers
    add_exception_handlers(app)

    # Include API routers
    include_routers(app)

    # Add health check endpoint
    add_health_check(app)

    return app


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    if hasattr(settings, "BACKEND_CORS_ORIGINS") and settings.BACKEND_CORS_ORIGINS:
        origins = [str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    elif settings.CORS_ORIGINS:
        origins = [str(origin).strip("/") for origin in settings.CORS_ORIGINS]
    else:
        origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )
    logger.info(f"🌐 CORS configured for origins: {', '.join(origins) if origins else 'all'}")


def include_routers(app: FastAPI) -> None:
    """Include all API routers."""
    # Authentication routes
    app.include_router(
        auth.router,
        prefix=f"{settings.API_V1_STR}/auth",
        tags=["Authentication"],  # This tag is now defined in auth.py
    )

    # API v1 routes
    api_router = APIRouter(prefix=settings.API_V1_STR)
    api_router.include_router(ai.router, prefix="/ai", tags=["AI"])
    api_router.include_router(health.router, tags=["Health"])
    # api_router.include_router(builds.router, tags=["Builds"])  # Replaced by builds_db
    api_router.include_router(chat.router, tags=["Chat"])
    api_router.include_router(export.router, tags=["Export"])
    api_router.include_router(learning.router, tags=["Learning"])
    api_router.include_router(meta.router, tags=["Meta"])
    api_router.include_router(scraper.router, tags=["Scraper"])
    # api_router.include_router(teams.router, tags=["Teams"])  # Replaced by teams_db
    api_router.include_router(builds_db.router, tags=["Builds"])
    api_router.include_router(teams_db.router, tags=["Teams"])
    api_router.include_router(websocket_mcm.router, tags=["WebSocket McM"])

    app.include_router(api_router)
    logger.info("🔄 API routers included")


def add_health_check(app: FastAPI) -> None:
    """Add health check endpoint."""

    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "environment": settings.ENVIRONMENT}


# Create the FastAPI application
app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
