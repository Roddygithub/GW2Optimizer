from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from app.core.logging import logger


class BusinessException(Exception):
    """Base class for custom business logic exceptions."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST, error_code: str = "BUSINESS_LOGIC_ERROR"):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.detail)

class InvalidCredentialsException(BusinessException):
    def __init__(self):
        super().__init__(detail="Incorrect email or password", status_code=status.HTTP_401_UNAUTHORIZED, error_code="INVALID_CREDENTIALS")

class AccountLockedException(BusinessException):
    def __init__(self):
        super().__init__(detail="Account is locked or inactive.", status_code=status.HTTP_403_FORBIDDEN, error_code="ACCOUNT_LOCKED")

class UserExistsException(BusinessException):
    def __init__(self, field: str):
        super().__init__(detail=f"{field.capitalize()} already registered", status_code=status.HTTP_409_CONFLICT, error_code=f"USER_{field.upper()}_EXISTS")


def add_exception_handlers(app: FastAPI) -> None:
    """Adds custom exception handlers to the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.warning(
            f"HTTP Exception: {exc.status_code} {exc.detail} for {request.method} {request.url} [ID: {correlation_id}]"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": "HTTP_EXCEPTION",
                "detail": exc.detail,
                "correlation_id": correlation_id},
        )

    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.warning(
            "Business exception occurred",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
                "method": request.method,
                "correlation_id": correlation_id,
            })
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "detail": exc.detail,
                "correlation_id": correlation_id
            })

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        
        # Standardize validation error response
        formatted_errors = {}
        for error in exc.errors():
            # Create a simple key from the error location tuple
            field_name = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            formatted_errors[field_name] = error["msg"]

        logger.warning(f"Validation Error: {formatted_errors} for {request.method} {request.url} [ID: {correlation_id}]")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": "One or more validation errors occurred.",
                "fields": formatted_errors,
                "correlation_id": correlation_id,
            })

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "N/A")
        logger.error(
            f"Unhandled Exception: {exc} for {request.method} {request.url} [ID: {correlation_id}]",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "detail": "An unexpected error occurred.",
                "correlation_id": correlation_id
            })