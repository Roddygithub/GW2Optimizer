"""
Sentry Debug Endpoint
Test endpoint to verify Sentry error tracking integration
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/sentry-debug")
async def trigger_error():
    """
    Trigger a test error for Sentry verification.

    This endpoint intentionally causes a division by zero error
    to test Sentry error tracking and performance monitoring.

    **WARNING**: Only use this in development/testing environments.
    """
    division_by_zero = 1 / 0
    return {"status": "This should never be reached"}
