"""
Custom exception handlers for the FastAPI application.

This module centralizes error handling to provide consistent,
structured error responses across the API.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from redis.exceptions import ConnectionError
from app.core.logging import logger


class BusinessException(Exception):
    """Base class for custom business logic exceptions."""

    def __init__(
        self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST, error_code: str = "BUSINESS_LOGIC_ERROR"
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.detail)


class UserExistsException(BusinessException):
    """Exception raised when a user already exists."""

    def __init__(self, detail: str = "User already exists"):
        super().__init__(detail, status.HTTP_409_CONFLICT, "USER_EXISTS")


class UserEmailExistsException(BusinessException):
    """Exception raised when an email is already registered."""

    def __init__(self, detail: str = "Email already registered"):
        super().__init__(detail, status.HTTP_409_CONFLICT, "USER_EMAIL_EXISTS")


class UserUsernameExistsException(BusinessException):
    """Exception raised when a username is already taken."""

    def __init__(self, detail: str = "Username already registered"):
        super().__init__(detail, status.HTTP_409_CONFLICT, "USER_USERNAME_EXISTS")


class InvalidCredentialsException(BusinessException):
    """Exception raised when credentials are invalid."""

    def __init__(self, detail: str = "Incorrect or invalid credentials"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS")


class AccountLockedException(BusinessException):
    """Exception raised when account is locked."""

    def __init__(self, detail: str = "Account is locked", status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(detail, status_code, "ACCOUNT_LOCKED")


def add_exception_handlers(app: FastAPI) -> None:
    """Adds custom exception handlers to the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)  # type: ignore[misc]
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.warning(
            f"HTTP Exception: {exc.status_code} {exc.detail} for {request.method} {request.url} [ID: {correlation_id}]"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": "HTTP_EXCEPTION", "detail": exc.detail, "correlation_id": correlation_id},
            headers=exc.headers or {},
        )

    @app.exception_handler(BusinessException)  # type: ignore[misc]
    async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.warning(f"Business Logic Error: {exc.error_code} - {exc.detail} [ID: {correlation_id}]")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "detail": exc.detail, "correlation_id": correlation_id},
        )

    @app.exception_handler(RequestValidationError)  # type: ignore[misc]
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")

        formatted_errors = {".".join(map(str, err["loc"][1:])): err["msg"] for err in exc.errors()}

        logger.warning(
            f"Validation Error: {formatted_errors} for {request.method} {request.url} [ID: {correlation_id}]"
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": "One or more validation errors occurred.",
                "fields": formatted_errors,
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(Exception)  # type: ignore[misc]
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, ConnectionError):
            raise exc
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.error(
            f"Unhandled Exception: {exc} for {request.method} {request.url} [ID: {correlation_id}]", exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "detail": "An unexpected error occurred. Please contact support.",
                "correlation_id": correlation_id,
            },
        )
