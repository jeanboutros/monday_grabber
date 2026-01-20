"""Core module containing base classes, types, exceptions, and logging configuration.

This module provides the foundational components for the monday_grabber package:

- **Protocols**: Abstract interfaces for dependency injection (HttpClient, QueryProvider)
- **Types**: Pydantic models and enums for configuration and API responses
- **Exceptions**: Hierarchical exception classes for error handling
- **Logging**: Centralized logging configuration utilities

All loggers are children of ``PANPAN.monday_grabber``. Pass a relative module path
to ``get_logger()`` to create a child logger.

Example::

    from monday_grabber.core import (
        configure_logging,
        get_logger,
        MondayAPIException,
        OutputFormat,
    )

    # Configure logging at application startup
    configure_logging(level="DEBUG")

    # Logger becomes PANPAN.monday_grabber.mymodule
    logger = get_logger("mymodule")

    # Use types and exceptions
    output_format = OutputFormat.CSV
"""

from .abc import HttpClient, QueryProvider, ConfigProvider
from .logging_config import (
    configure_logging,
    get_logger,
    is_configured,
    ROOT_LOGGER_NAME,
    ENV_LOG_LEVEL,
    ENV_LOG_FORMAT,
)
from .types import (
    PaginationConfig,
    QueryConfig,
    ErrorCode,
    ErrorLocation,
    ErrorExtensions,
    MondayError,
    MondayAPIResponse,
    DataType,
    ColumnConfig,
    OutputFormat,
    TableConfig,
    EntityType,
)
from .exceptions import (
    MondayAPIException,
    MondayApplicationError,
    MondayClientError,
    MondayServerError,
)

__all__ = [
    # Protocols
    "HttpClient",
    "QueryProvider",
    "ConfigProvider",
    # Logging
    "configure_logging",
    "get_logger",
    "is_configured",
    "ROOT_LOGGER_NAME",
    "ENV_LOG_LEVEL",
    "ENV_LOG_FORMAT",
    # Types
    "PaginationConfig",
    "QueryConfig",
    "ErrorCode",
    "ErrorLocation",
    "ErrorExtensions",
    "MondayError",
    "MondayAPIResponse",
    "DataType",
    "ColumnConfig",
    "OutputFormat",
    "TableConfig",
    "EntityType",
    # Exceptions
    "MondayAPIException",
    "MondayApplicationError",
    "MondayClientError",
    "MondayServerError",
]
