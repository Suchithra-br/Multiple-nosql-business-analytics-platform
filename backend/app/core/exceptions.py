"""
Centralized Application Exceptions.

Defines domain-specific exception types for controlled error handling.
"""

from typing import Optional, Any


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class ResourceNotFoundError(AppException):
    """Raised when a requested resource (order, customer, etc.) is not found."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="RESOURCE_NOT_FOUND", status_code=404, details=details)


class ValidationError(AppException):
    """Raised when request query parameters or business inputs fail validation."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400, details=details)


class DatabaseConnectionError(AppException):
    """Raised when a database service is unreachable or encounters a driver error."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, code="DATABASE_UNAVAILABLE", status_code=503, details=details)
