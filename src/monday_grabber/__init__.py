"""Monday Grabber - A Python client for Monday.com GraphQL API.

This package provides a clean interface for interacting with the
Monday.com API with built-in pagination and error handling.

Example::

    from monday_grabber import MondayClient, QueryExecutor, QueryLoader, ConfigLoader
    from pathlib import Path

    client = MondayClient(api_key="your_key")
    loader = QueryLoader(queries_dir=Path("queries"))
    config = ConfigLoader(config_path=Path("config/queries.yaml"))

    executor = QueryExecutor(
        client=client,
        query_loader=loader,
        config_loader=config,
    )

    result = executor.execute_configured(
        query_name="get_board_items",
        target_board_ids=[123456],
    )
"""

# Client
from monday_grabber.client import MondayClient, ResponseHandler

# Config
from monday_grabber.config import ConfigLoader

# Core
from monday_grabber.core import (
    ConfigProvider,
    ErrorCode,
    ErrorExtensions,
    ErrorLocation,
    HttpClient,
    MondayAPIException,
    MondayAPIResponse,
    MondayApplicationError,
    MondayClientError,
    MondayError,
    MondayServerError,
    PaginationConfig,
    QueryConfig,
    QueryProvider,
    DataType,
    ColumnConfig,
    OutputFormat,
    TableConfig,
    EntityType,
    configure_logging,
    get_logger,
)

# GraphQL
from monday_grabber.graphql import (
    PaginationHandler,
    QueryExecutor,
    QueryLoader,
    ResponseParser,
)

# Parser
from monday_grabber.parser import (
    TableParser,
    DataFrameWriter,
    CsvWriter,
    JsonWriter,
    ParquetWriter,
    WriterFactory,
)

# CLI entry point
from monday_grabber.__main__ import main

__version__ = "0.2.0"

__all__ = [
    # Client
    "MondayClient",
    "ResponseHandler",
    # Config
    "ConfigLoader",
    # GraphQL
    "QueryExecutor",
    "QueryLoader",
    "ResponseParser",
    "PaginationHandler",
    # Parser
    "TableParser",
    "DataFrameWriter",
    "CsvWriter",
    "JsonWriter",
    "ParquetWriter",
    "WriterFactory",
    # Core types
    "PaginationConfig",
    "QueryConfig",
    "DataType",
    "ColumnConfig",
    "OutputFormat",
    "TableConfig",
    "EntityType",
    # Core protocols
    "HttpClient",
    "QueryProvider",
    "ConfigProvider",
    # Logging
    "configure_logging",
    "get_logger",
    # Exceptions
    "MondayAPIException",
    "MondayApplicationError",
    "MondayClientError",
    "MondayServerError",
    # Error types
    "ErrorCode",
    "MondayAPIResponse",
    "MondayError",
    "ErrorExtensions",
    "ErrorLocation",
    # CLI
    "main",
]
