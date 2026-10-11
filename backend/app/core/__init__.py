"""
Core Module.

Provides centralized configuration, logging, exceptions, and error handling.
"""

from backend.app.core.config import settings
from backend.app.core.logging_config import setup_logging
from backend.app.core.exceptions import (
    AppException,
    ResourceNotFoundError,
    ValidationError,
    DatabaseConnectionError,
)
from backend.app.core.error_handlers import register_error_handlers

__all__ = [
    "settings",
    "setup_logging",
    "AppException",
    "ResourceNotFoundError",
    "ValidationError",
    "DatabaseConnectionError",
    "register_error_handlers",
]
