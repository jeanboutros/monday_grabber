# Copilot Instructions for Monday Grabber

This document defines the project structure, principles, design patterns, and architecture for the `monday_grabber` Python package. Follow these guidelines when generating code.

## Project Overview

**monday_grabber** is a Python 3.12+ client for the Monday.com GraphQL API. It ingests data from Monday.com boards, workspaces, and other entities, transforms it using jq expressions, and exports to various file formats (CSV, JSON, Parquet).

## Directory Structure

```
monday_grabber/
├── src/monday_grabber/
│   ├── __init__.py          # Package exports
│   ├── __main__.py           # CLI entry point (argparse)
│   ├── client/               # HTTP client layer
│   │   ├── monday_client.py  # Low-level HTTP client
│   │   └── response_handler.py
│   ├── config/               # Configuration loading
│   │   └── config_loader.py  # YAML config loader
│   ├── core/                 # Core abstractions
│   │   ├── abc.py            # Protocols (interfaces)
│   │   ├── exceptions.py     # Exception hierarchy
│   │   ├── logging_config.py # Centralized logging
│   │   └── types.py          # Pydantic models & enums
│   ├── graphql/              # GraphQL operations
│   │   ├── query_executor.py # Query execution with pagination
│   │   ├── query_loader.py   # Load .graphql files
│   │   ├── pagination.py     # Pagination handling
│   │   └── response_parser.py
│   ├── parser/               # Data transformation
│   │   ├── table_parser.py   # jq + Polars transformation
│   │   └── writers/          # Output format writers
│   │       ├── protocol.py   # DataFrameWriter protocol
│   │       ├── csv_writer.py
│   │       ├── json_writer.py
│   │       ├── parquet_writer.py
│   │       └── factory.py    # WriterFactory
│   └── queries/              # .graphql query files
├── config/
│   └── queries.yaml          # Query and board configurations
├── tests/
└── pyproject.toml
```

## Architecture Principles

### 1. Protocol-Based Dependency Injection

Use `typing.Protocol` for abstractions, not abstract base classes. This enables duck typing and easier testing.

```python
from typing import Protocol

class HttpClient(Protocol):
    """Protocol for HTTP client implementations."""
    
    def post(self, *, query: str, variables: dict | None = None) -> dict:
        ...
```

Classes depend on protocols, not concrete implementations:

```python
class QueryExecutor:
    def __init__(self, *, client: HttpClient, query_loader: QueryProvider):
        self._client = client
        self._query_loader = query_loader
```

### 2. Factory Pattern for Extensibility

Use factories for creating instances of protocol implementations:

```python
class WriterFactory:
    """Factory for creating DataFrameWriter instances."""
    
    def create(self, *, format: OutputFormat) -> DataFrameWriter:
        match format:
            case OutputFormat.CSV:
                return CsvWriter()
            case OutputFormat.JSON:
                return JsonWriter()
            case OutputFormat.PARQUET:
                return ParquetWriter()
```

### 3. Pydantic Models for Configuration

All configuration and API response types use Pydantic v2 models:

```python
from pydantic import BaseModel, Field

class QueryConfig(BaseModel):
    """Configuration for a single query."""
    
    name: str = Field(..., description="Query identifier")
    graphql_file: str = Field(..., description="Path to .graphql file")
    entity_type: EntityType = Field(default=EntityType.BOARD)
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
```

### 4. Enums with StrEnum

Use `StrEnum` for string-based enumerations:

```python
from enum import StrEnum

class EntityType(StrEnum):
    """Types of Monday.com entities."""
    BOARD = "board"
    WORKSPACE = "workspace"
    USER = "user"
    TEAM = "team"
    FOLDER = "folder"
    ITEM = "item"
    COLUMN = "column"
```

## Logging Standards

### Logger Hierarchy

All loggers are children of `PANPAN.monday_grabber`. Use relative paths:

```python
from monday_grabber.core.logging_config import get_logger

# In client/monday_client.py:
logger = get_logger("client.monday_client")
# Result: PANPAN.monday_grabber.client.monday_client

# In __main__.py:
logger = get_logger("__main__")
# Result: PANPAN.monday_grabber.__main__
```

### Log Format

Default format includes logger name, filename, and line number at the end:

```
%(asctime)s | %(levelname)-8s | %(message)s [%(name)s @ %(filename)s:%(lineno)d]
```

Example output:
```
2026-01-20T19:24:50Z | INFO     | Starting workflow [PANPAN.monday_grabber.__main__ @ __main__.py:480]
```

### Environment Variables

- `MONDAY_GRABBER__LOG_LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `MONDAY_GRABBER__LOG_FORMAT`: Override log format string

Priority: CLI arguments > Environment variables > Defaults

### Logging Patterns

```python
def my_function(data: dict) -> Result:
    """Process data and return result."""
    logger.info("Entering my_function")
    logger.debug("Input data: %s", data)
    
    # Processing logic with inline comments explaining steps
    # -------------------------------------------------------------------------
    # Transform the data using jq expression
    # -------------------------------------------------------------------------
    result = transform(data)
    
    logger.debug("Transformed result: %s", result)
    logger.info("Exiting my_function")
    return result
```

## Documentation Standards (Sphinx)

### Module Docstrings

```python
"""Short description of the module.

Extended description explaining purpose and usage.

Example::

    from monday_grabber.module import MyClass
    
    obj = MyClass(param="value")
    result = obj.method()

Attributes:
    CONSTANT: Description of module-level constant.
"""
```

### Function/Method Docstrings

Use Sphinx-style `:param:`, `:returns:`, `:raises:`:

```python
def execute_query(
    self,
    *,
    query_name: str,
    board_ids: list[int],
) -> list[dict]:
    """Execute a configured query against specified boards.
    
    :param query_name: Name of the query from queries.yaml.
    :param board_ids: List of Monday.com board IDs to query.
    :returns: List of response dictionaries from the API.
    :raises MondayAPIException: On API errors.
    :raises FileNotFoundError: If query file not found.
    
    Example::
    
        results = executor.execute_query(
            query_name="get_board_items",
            board_ids=[123456, 789012],
        )
    """
```

### Class Docstrings

```python
class MondayClient:
    """HTTP client for Monday.com GraphQL API.
    
    Handles authentication and HTTP transport only.
    Use QueryExecutor for higher-level operations.
    
    :param api_key: Monday.com API key.
    :param endpoint_url: API endpoint URL (optional).
    
    Example::
    
        client = MondayClient(api_key="your_key")
        response = client.post(query="{ me { name } }")
    """
```

## Code Style

### Keyword-Only Arguments

Use `*` to enforce keyword-only arguments for functions with multiple parameters:

```python
def __init__(
    self,
    *,
    api_key: str,
    endpoint_url: str | None = None,
) -> None:
```

### Inline Comments with Separators

Use comment blocks to explain code sections:

```python
# ---------------------------------------------------------------------------
# Validate that API key is provided
# ---------------------------------------------------------------------------
if not api_key:
    logger.error("API key is required but not provided")
    raise ValueError("API key is required")

# ---------------------------------------------------------------------------
# Store configuration
# ---------------------------------------------------------------------------
self._api_key = api_key
self._endpoint_url = endpoint_url or self.DEFAULT_ENDPOINT
```

### Type Hints

Always use modern Python 3.12+ type hints:

```python
# Use | instead of Union
def process(value: str | None = None) -> dict[str, Any]:
    ...

# Use list, dict, tuple directly (no typing imports)
def get_items(ids: list[int]) -> dict[str, list[str]]:
    ...
```

### Private Attributes

Prefix private attributes with underscore:

```python
class MondayClient:
    def __init__(self, *, api_key: str):
        self._api_key = api_key
        self._headers = self._create_headers()
```

## Exception Handling

### Exception Hierarchy

```python
MondayAPIException          # Base exception
├── MondayClientError       # 4xx client errors
├── MondayServerError       # 5xx server errors
└── MondayApplicationError  # API application errors
```

### Raising Exceptions

```python
from monday_grabber.core import MondayAPIException, MondayClientError

if response.status_code >= 400:
    logger.error("API request failed: %s", response.text)
    raise MondayClientError(
        message="Failed to fetch board",
        status_code=response.status_code,
        error_code=ErrorCode.BAD_REQUEST,
    )
```

## CLI Pattern

The CLI uses argparse with the following conventions:

```python
def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monday_grabber",
        description="Ingest data from Monday.com boards.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Short and long options
    parser.add_argument("-q", "--query", type=str, help="Query name")
    parser.add_argument("-b", "--boards", nargs="+", help="Board names")
    parser.add_argument("-f", "--format", choices=["csv", "json", "parquet"])
    
    # Flags
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    
    return parser
```

## Testing Patterns

### Test File Naming

- `test_<module_name>.py` for unit tests
- `verify_<feature>.py` for integration/verification tests

### Mocking Protocols

```python
from unittest.mock import Mock

def test_query_executor():
    mock_client = Mock(spec=HttpClient)
    mock_client.post.return_value = {"data": {"boards": []}}
    
    executor = QueryExecutor(client=mock_client, query_loader=mock_loader)
    result = executor.execute(query_name="test")
    
    mock_client.post.assert_called_once()
```

## Configuration (queries.yaml)

```yaml
queries:
  get_board_items:
    graphql_file: get_board_items.graphql
    entity_type: board
    pagination:
      enabled: true
      variable: cursor
    jq_transform: ".boards[].items_page.items[]"
    table_config:
      columns:
        - name: id
          data_type: string
        - name: name
          data_type: string

boards:
  main_board:
    id: 18310022893
    name: "Main Project Board"
```

## Key Dependencies

- **Python 3.12+**: Required version (3.13+ recommended)
- **pydantic >= 2.0.0**: Data validation and models
- **polars >= 1.37.1**: DataFrame operations
- **jq >= 1.8.0**: JSON transformation
- **requests**: HTTP client
- **pyyaml**: YAML configuration
- **python-dotenv**: Environment variable loading

## Adding New Features

### New Entity Type

1. Add to `EntityType` enum in `core/types.py`
2. Create query in `queries/` directory
3. Add configuration in `config/queries.yaml`
4. Add CLI support if needed

### New Output Format

1. Create writer class implementing `DataFrameWriter` protocol
2. Register in `WriterFactory`
3. Add to `OutputFormat` enum

### New Configuration Option

1. Add field to appropriate Pydantic model in `core/types.py`
2. Update YAML schema documentation
3. Handle in relevant loader/executor
