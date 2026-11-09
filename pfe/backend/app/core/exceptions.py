"""
Custom exceptions for the application
"""
from fastapi import HTTPException, status
from typing import Any



class AppException(Exception):
    """Base application exception"""
    pass


class NotFoundError(AppException):
    """Resource not found exception"""
    pass


class ValidationError(AppException):
    """Validation error exception"""
    pass


class ScrapingError(AppException):
    """Scraping operation error"""
    pass


class DatabaseError(AppException):
    """Database operation error"""
    pass


# HTTP Exception helpers
def not_found_exception(resource: str, resource_id: Any) -> HTTPException:
    """Create a 404 Not Found exception"""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} with id {resource_id} not found"
    )


def validation_exception(message: str) -> HTTPException:
    """Create a 422 Validation Error exception"""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=message
    )


def unauthorized_exception(message: str = "Not authenticated") -> HTTPException:
    """Create a 401 Unauthorized exception"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(message: str = "Not enough permissions") -> HTTPException:
    """Create a 403 Forbidden exception"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )

