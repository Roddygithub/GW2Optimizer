"""Health check endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.ai.ollama_service import OllamaService

router = APIRouter()


@router.get("/health")
async def health_check() -> JSONResponse:
    """Basic health check."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "GW2Optimizer API",
            "version": "1.0.0",
        }
    )


@router.get("/health/ollama")
async def ollama_health() -> JSONResponse:
    """Check Ollama service health."""
    ollama_service = OllamaService()
    is_healthy = await ollama_service.check_health()

    return JSONResponse(
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "Ollama",
            "available": is_healthy,
        },
        status_code=200 if is_healthy else 503,
    )


@router.get("/health/all")
async def full_health_check() -> JSONResponse:
    """Complete health check of all services."""
    ollama_service = OllamaService()
    ollama_healthy = await ollama_service.check_health()

    return JSONResponse(
        content={
            "status": "healthy" if ollama_healthy else "degraded",
            "services": {
                "api": {"status": "healthy"},
                "ollama": {"status": "healthy" if ollama_healthy else "unhealthy"},
                "database": {"status": "healthy"},  # TODO: Implement DB check
            },
        }
    )
