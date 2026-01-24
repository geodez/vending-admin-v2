"""
Validation middleware for API endpoints.
Provides common validation patterns and error handling.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Callable, Any, Optional, TypeVar, Generic
from functools import wraps
from app.api.middleware.error_handlers import BusinessLogicError

T = TypeVar('T')


class ValidationMiddleware:
    """Middleware for common validation patterns."""

    @staticmethod
    def validate_entity_exists(
        entity_getter: Callable[[Session, Any], Optional[T]],
        entity_id: Any,
        entity_name: str,
        db: Session
    ) -> T:
        """
        Validate that an entity exists and return it.

        Args:
            entity_getter: Function to get entity (e.g., crud.get_location)
            entity_id: ID of the entity to find
            entity_name: Human-readable name for error messages
            db: Database session

        Returns:
            The found entity

        Raises:
            HTTPException: If entity not found
        """
        entity = entity_getter(db, entity_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} not found"
            )
        return entity

    @staticmethod
    def handle_db_operation(
        operation: Callable[[], T],
        error_msg: str = "Database operation failed",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> T:
        """
        Handle database operations with error handling.

        Args:
            operation: Function to execute
            error_msg: Error message for exceptions
            status_code: HTTP status code for errors

        Returns:
            Result of the operation

        Raises:
            HTTPException: If operation fails
        """
        try:
            return operation()
        except BusinessLogicError:
            # Let BusinessLogicError bubble up to be handled by global error handler
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status_code,
                detail=f"{error_msg}: {str(e)}"
            )

    @staticmethod
    def validate_bulk_operation(
        codes: list,
        max_batch_size: int = 100
    ) -> None:
        """
        Validate bulk operation parameters.

        Args:
            codes: List of entity codes/IDs
            max_batch_size: Maximum allowed batch size

        Raises:
            HTTPException: If validation fails
        """
        if not codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No codes provided"
            )

        if len(codes) > max_batch_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds maximum of {max_batch_size}"
            )


def with_entity_validation(
    entity_getter: Callable[[Session, Any], Optional[T]],
    entity_name: str
):
    """
    Decorator for endpoints that need entity validation.

    Args:
        entity_getter: Function to get entity
        entity_name: Human-readable entity name

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract db and entity_id from kwargs
            db = kwargs.get('db')
            entity_id = kwargs.get('entity_id') or kwargs.get('location_id') or kwargs.get('drink_id')

            if db and entity_id is not None:
                ValidationMiddleware.validate_entity_exists(
                    entity_getter, entity_id, entity_name, db
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator