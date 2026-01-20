"""Centralized logging configuration for Monday Grabber.

This module provides a consistent logging setup across the entire application.
It should be imported and configured once at application startup.

All loggers are children of the root logger ``PANPAN.monday_grabber``. When
modules request a logger with a relative name like ``client.monday_client``,
they receive ``PANPAN.monday_grabber.client.monday_client``.

Environment Variables:
    MONDAY_GRABBER__LOG_LEVEL: Override the default log level (DEBUG, INFO, etc.).
        CLI arguments take precedence over this variable.
    MONDAY_GRABBER__LOG_FORMAT: Override the default log format string.

Example::

    from monday_grabber.core.logging_config import configure_logging, get_logger

    # Configure logging at startup (typically in __main__.py)
    configure_logging(level="INFO")

    # Get a logger for a specific module (becomes PANPAN.monday_grabber.client.monday_client)
    logger = get_logger("client.monday_client")
    logger.info("Application started")

Logging Levels:
    - DEBUG: Detailed information for debugging (function internals, data values)
    - INFO: Confirmation that things work as expected (function entry/exit)
    - WARNING: Something unexpected happened but execution continues
    - ERROR: A serious problem that prevented a function from completing
    - CRITICAL: The program cannot continue

Attributes:
    ROOT_LOGGER_NAME: Base logger name (PANPAN.monday_grabber).
    DEFAULT_FORMAT: Default log message format.
    DEFAULT_LEVEL: Default logging level (INFO)."""

import logging
import os
import sys
from typing import Literal

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT_LOGGER_NAME = "PANPAN.monday_grabber"
"""Root logger name. All module loggers are children of this logger."""

ENV_LOG_LEVEL = "MONDAY_GRABBER__LOG_LEVEL"
"""Environment variable for overriding the default log level."""

ENV_LOG_FORMAT = "MONDAY_GRABBER__LOG_FORMAT"
"""Environment variable for overriding the default log format."""

DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(message)s [%(name)s @ %(filename)s:%(lineno)d]"
)
"""Default log message format with timestamp, level, message, logger name, file, and line."""

DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
"""ISO 8601 date format for timestamps."""

DEFAULT_LEVEL = logging.INFO
"""Default logging level."""

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
"""Type alias for valid logging level strings."""

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_configured: bool = False
"""Track whether logging has been configured."""


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def configure_logging(
    *,
    level: LogLevel | int | None = None,
    format_string: str | None = None,
    date_format: str = DEFAULT_DATE_FORMAT,
    stream: object | None = None,
) -> None:
    """Configure application-wide logging settings.

    This function should be called once at application startup, typically
    in the __main__.py file before any other imports that might log.

    Priority order for log level (highest to lowest):
        1. ``level`` parameter (CLI arguments should pass this)
        2. ``MONDAY_GRABBER__LOG_LEVEL`` environment variable
        3. Default: INFO

    Priority order for log format:
        1. ``format_string`` parameter
        2. ``MONDAY_GRABBER__LOG_FORMAT`` environment variable
        3. Default format with logger name, filename, and line number

    :param level: Logging level as string ("DEBUG", "INFO", etc.) or int.
        If None, uses env var or default.
    :param format_string: Format string for log messages.
        If None, uses env var or default.
    :param date_format: Format string for timestamps.
    :param stream: Output stream (defaults to sys.stderr).

    Example::

        from monday_grabber.core.logging_config import configure_logging

        # Basic setup - uses env vars or defaults
        configure_logging()

        # Debug mode for development (overrides env var)
        configure_logging(level="DEBUG")

        # Custom format
        configure_logging(
            level="INFO",
            format_string="%(levelname)s - %(message)s",
        )
    """
    global _configured

    # Resolve log level with priority: parameter > env var > default
    # -------------------------------------------------------------------------
    # CLI arguments should pass the level parameter, which takes precedence.
    # If not provided, check environment variable, then fall back to default.
    # -------------------------------------------------------------------------
    if level is not None:
        # Explicit level provided (e.g., from CLI)
        if isinstance(level, str):
            numeric_level = getattr(logging, level.upper(), DEFAULT_LEVEL)
        else:
            numeric_level = level
    else:
        # Check environment variable
        env_level = os.environ.get(ENV_LOG_LEVEL)
        if env_level:
            numeric_level = getattr(logging, env_level.upper(), DEFAULT_LEVEL)
        else:
            numeric_level = DEFAULT_LEVEL

    # Resolve format string with priority: parameter > env var > default
    # -------------------------------------------------------------------------
    if format_string is not None:
        resolved_format = format_string
    else:
        resolved_format = os.environ.get(ENV_LOG_FORMAT, DEFAULT_FORMAT)

    # Use stderr as default stream for logging
    # -------------------------------------------------------------------------
    # stderr is preferred over stdout for logs because it keeps logs
    # separate from program output, useful for piping
    # -------------------------------------------------------------------------
    if stream is None:
        stream = sys.stderr

    # Create and configure the PANPAN.monday_grabber root logger
    # -------------------------------------------------------------------------
    # We configure this named logger so all child loggers inherit settings.
    # Using a named root allows isolation from other libraries' logging.
    # -------------------------------------------------------------------------
    root_logger = logging.getLogger(ROOT_LOGGER_NAME)
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates on reconfiguration
    # -------------------------------------------------------------------------
    # This is important when the function is called multiple times
    # (e.g., in tests or when reloading configuration)
    # -------------------------------------------------------------------------
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create stream handler with formatting
    # -------------------------------------------------------------------------
    # StreamHandler writes log records to a stream (default: stderr)
    # -------------------------------------------------------------------------
    handler = logging.StreamHandler(stream)
    handler.setLevel(numeric_level)

    # Create formatter and attach to handler
    # -------------------------------------------------------------------------
    # The formatter controls how log records are rendered as strings
    # -------------------------------------------------------------------------
    formatter = logging.Formatter(resolved_format, datefmt=date_format)
    handler.setFormatter(formatter)

    # Attach handler to root logger
    root_logger.addHandler(handler)

    # Mark as configured
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance as a child of PANPAN.monday_grabber.

    This function returns a logger that is a child of the root
    ``PANPAN.monday_grabber`` logger. Pass a relative module path
    like ``client.monday_client`` to get a logger named
    ``PANPAN.monday_grabber.client.monday_client``.

    :param name: Logger name relative to PANPAN.monday_grabber.
        For example, ``client.monday_client`` becomes
        ``PANPAN.monday_grabber.client.monday_client``.
    :returns: Configured logger instance.

    Example::

        from monday_grabber.core.logging_config import get_logger

        # In client/monday_client.py:
        logger = get_logger("client.monday_client")
        # Logger name: PANPAN.monday_grabber.client.monday_client

        def my_function():
            logger.info("Entering my_function")
            logger.debug("Processing data: %s", data)
            logger.info("Exiting my_function")
    """
    return logging.getLogger(ROOT_LOGGER_NAME).getChild(name)


def is_configured() -> bool:
    """Check if logging has been configured.

    :returns: True if configure_logging() has been called.

    Example::

        if not is_configured():
            configure_logging()
    """
    return _configured
