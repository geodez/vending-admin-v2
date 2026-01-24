"""
Centralized error handling for API endpoints.
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, DataError
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register global error handlers for the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "type": "http_error",
                "path": str(request.url)
            }
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity errors."""
        logger.error(f"Database integrity error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Database constraint violation. This operation would create invalid data.",
                "type": "integrity_error",
                "path": str(request.url)
            }
        )

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError):
        """Handle database data errors."""
        logger.error(f"Database data error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Invalid data format or value.",
                "type": "data_error",
                "path": str(request.url)
            }
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "type": "validation_error",
                "errors": exc.errors(),
                "path": str(request.url)
            }
        )

    @app.exception_handler(BusinessLogicError)
    async def business_logic_error_handler(request: Request, exc: BusinessLogicError):
        """Handle business logic errors."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "type": "business_logic_error",
                "path": str(request.url)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": "internal_error",
                "path": str(request.url)
            }
        )


class BusinessLogicError(Exception):
    """Custom exception for business logic errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def handle_business_error(error_msg: str, status_code: int = 400):
    """
    Helper function to raise business logic errors.

    Args:
        error_msg: Error message
        status_code: HTTP status code
    """
    raise BusinessLogicError(error_msg, status_code)