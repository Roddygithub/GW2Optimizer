"""
Chat API endpoints for interacting with the AI assistant.

This module provides endpoints for sending chat messages to the AI assistant
and receiving responses with build suggestions and recommendations.
"""

import time
from typing import Dict, Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import logger
from app.core.circuit_breaker import CircuitBreakerError
from app.models.chat import ChatRequest, ChatResponse
from app.services.ai.chat_service import ChatService

router = APIRouter(prefix="/api/v1/ai", tags=["AI Chat"])
chat_service = ChatService()

# Track request metrics
REQUEST_METRICS = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "avg_response_time": 0.0,
}


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a chat message",
    description="""
    Send a message to the AI assistant and receive a response with build suggestions.
    
    The AI can:
    - Answer questions about GW2 builds and meta
    - Parse and analyze GW2Skill links
    - Suggest optimized team compositions
    - Provide build recommendations based on role and game mode
    - Explain build mechanics and synergies
    """,
    responses={
        200: {
            "description": "Successful response from the AI assistant",
            "content": {
                "application/json": {
                    "example": {
                        "response": "Here's a great build for your Guardian in WvW zergs...",
                        "suggestions": ["Show me a DPS build", "What about a support Firebrand?"],
                        "builds": [{"name": "Heal Firebrand", "profession": "Guardian"}],
                        "metadata": {"model_used": "llama3", "response_time": 1.23},
                    }
                }
            },
        },
        400: {"description": "Invalid request format or missing required fields"},
        429: {"description": "Too many requests, rate limit exceeded"},
        500: {"description": "Internal server error"},
        503: {"description": "Service temporarily unavailable"},
    },
)
async def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    """
    Process a chat message and return an AI-generated response.

    Args:
        request: The chat request containing the message and conversation history
        http_request: The raw HTTP request for logging and metrics

    Returns:
        ChatResponse containing the AI's response, suggestions, and build information

    Raises:
        HTTPException: If there's an error processing the request
    """
    start_time = time.time()
    REQUEST_METRICS["total_requests"] += 1

    try:
        # Log the incoming request (without sensitive data)
        logger.info(
            "Processing chat message",
            extra={
                "message_preview": request.message[:100],
                "history_length": len(request.conversation_history or []),
                "client_ip": http_request.client.host if http_request.client else None,
                "user_agent": http_request.headers.get("user-agent"),
            },
        )

        # Process the message through the chat service
        response = await chat_service.process_message(request)

        # Calculate and log response time
        response_time = time.time() - start_time
        REQUEST_METRICS["successful_requests"] += 1
        REQUEST_METRICS["avg_response_time"] = (
            REQUEST_METRICS["avg_response_time"] * (REQUEST_METRICS["successful_requests"] - 1) + response_time
        ) / REQUEST_METRICS["successful_requests"]

        # Add performance metrics to response metadata
        if not response.metadata:
            response.metadata = {}
        response.metadata.update(
            {"response_time": round(response_time, 3), "request_id": http_request.state.get("request_id", "unknown")}
        )

        logger.info(
            "Successfully processed chat message",
            extra={
                "response_time": f"{response_time:.3f}s",
                "response_length": len(response.response),
                "suggestions_count": len(response.suggestions),
            },
        )

        return response

    except CircuitBreakerError as e:
        # Handle circuit breaker open scenario
        REQUEST_METRICS["failed_requests"] += 1
        logger.warning(
            "Chat service unavailable (circuit breaker open)",
            extra={"error": str(e), "circuit_state": e.circuit_breaker.state},
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "Chat service is currently unavailable. Please try again later.",
                "code": "service_unavailable",
                "retry_after": 60,  # seconds
            },
        )

    except Exception as e:
        # Log the full error for debugging
        REQUEST_METRICS["failed_requests"] += 1
        logger.error(
            "Error processing chat message", exc_info=True, extra={"error": str(e), "request_data": request.dict()}
        )

        # Return a user-friendly error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred while processing your message.",
                "code": "internal_server_error",
            },
        )

    finally:
        # Log request completion with timing
        logger.debug("Chat request completed", extra={"processing_time": f"{time.time() - start_time:.3f}s"})


# Track application startup time for uptime calculation
APP_START_TIME = time.time()


@router.get("/health", include_in_schema=False)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancing.

    Returns:
        Dict containing service status, version, and metrics
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "metrics": {**REQUEST_METRICS, "uptime": time.time() - APP_START_TIME, "timestamp": time.time()},
    }
