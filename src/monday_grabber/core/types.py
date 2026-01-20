"""Type definitions and Pydantic models for Monday Grabber.

This module contains all the data models and type definitions used throughout
the application. Models are built using Pydantic for validation and serialization.

Example::

    from monday_grabber.core.types import (
        QueryConfig,
        PaginationConfig,
        TableConfig,
        EntityType,
    )

    # Create a query configuration
    config = QueryConfig.from_dict(
        name="get_board_items",
        data={
            "entity_type": "board",
            "graphql_file": "get_board_items.graphql",
            "pagination": {"enabled": True},
        }
    )

Attributes:
    ErrorCode: Enumeration of Monday.com API error codes.
    DataType: Supported column data types for transformation.
    OutputFormat: Supported file output formats.
    EntityType: Types of Monday.com entities (boards, workspaces, users, etc.).
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    """Known Monday.com API error codes."""

    # 2xx Application-level errors
    API_TEMPORARILY_BLOCKED = "API_TEMPORARILY_BLOCKED"
    COLUMN_VALUE_EXCEPTION = "ColumnValueException"
    CORRECTED_VALUE_EXCEPTION = "CorrectedValueException"
    CREATE_BOARD_EXCEPTION = "CreateBoardException"
    INVALID_ARGUMENT_EXCEPTION = "InvalidArgumentException"
    INVALID_BOARD_ID_EXCEPTION = "InvalidBoardIdException"
    INVALID_COLUMN_ID_EXCEPTION = "InvalidColumnIdException"
    INVALID_USER_ID_EXCEPTION = "InvalidUserIdException"
    INVALID_VERSION_EXCEPTION = "InvalidVersionException"
    ITEM_NAME_TOO_LONG_EXCEPTION = "ItemNameTooLongException"
    ITEMS_LIMITATION_EXCEPTION = "ItemsLimitationException"
    MISSING_REQUIRED_PERMISSIONS = "missingRequiredPermissions"
    PARSE_ERROR = "ParseError"
    RESOURCE_NOT_FOUND_EXCEPTION = "ResourceNotFoundException"

    # 4xx Client errors
    BAD_REQUEST = "BadRequest"
    JSON_PARSE_EXCEPTION = "JsonParseException"
    UNAUTHORIZED = "Unauthorized"
    YOUR_IP_IS_RESTRICTED = "YourIpIsRestricted"
    USER_UNAUTHORIZED_EXCEPTION = "UserUnauthorizedException"
    USER_ACCESS_DENIED = "USER_ACCESS_DENIED"
    DELETE_LAST_GROUP_EXCEPTION = "DeleteLastGroupException"
    RECORD_INVALID_EXCEPTION = "RecordInvalidException"
    RESOURCE_LOCKED = "ResourceLocked"
    MAX_CONCURRENCY_EXCEEDED = "maxConcurrencyExceeded"
    RATE_LIMIT_EXCEEDED = "RateLimitExceeded"
    COMPLEXITY_BUDGET_EXHAUSTED = "COMPLEXITY_BUDGET_EXHAUSTED"
    IP_RATE_LIMIT_EXCEEDED = "IP_RATE_LIMIT_EXCEEDED"

    # 5xx Server errors
    INTERNAL_SERVER_ERROR = "InternalServerError"

    # Unknown
    UNKNOWN = "Unknown"


class ErrorLocation(BaseModel):
    """Location of an error in a GraphQL query.

    :param line: Line number.
    :param column: Column number.
    """

    line: int
    column: int


class ErrorExtensions(BaseModel):
    """Additional error information from API response.

    :param code: Error code string.
    :param error_data: Extra error details.
    :param status_code: HTTP status code if available.
    """

    code: str = ErrorCode.UNKNOWN.value
    error_data: dict[str, Any] = Field(default_factory=dict)
    status_code: int | None = None


class MondayError(BaseModel):
    """A single error from the Monday.com API response.

    :param message: Error message.
    :param locations: Locations in query where error occurred.
    :param path: Path to the field that caused the error.
    :param extensions: Additional error information.
    """

    message: str
    locations: list[ErrorLocation] = Field(default_factory=list)
    path: list[str] = Field(default_factory=list)
    extensions: ErrorExtensions = Field(default_factory=ErrorExtensions)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MondayError":
        """Create from API response dictionary.

        :param data: Error dictionary from API.
        :returns: MondayError instance.
        """
        locations = [
            ErrorLocation(line=loc["line"], column=loc["column"])
            for loc in data.get("locations", [])
        ]

        extensions_data = data.get("extensions", {})
        extensions = ErrorExtensions(
            code=extensions_data.get("code", ErrorCode.UNKNOWN.value),
            error_data=extensions_data.get("error_data", {}),
            status_code=extensions_data.get("status_code"),
        )

        return cls(
            message=data["message"],
            locations=locations,
            path=data.get("path", []),
            extensions=extensions,
        )


class MondayAPIResponse(BaseModel):
    """Complete Monday.com API response.

    :param data: Response data (may be partial if errors exist).
    :param errors: List of errors.
    :param account_id: Account ID if available.
    :param request_id: Request ID for debugging.
    :param retry_after: Seconds to wait before retry.
    """

    data: Any = None
    errors: list[MondayError] = Field(default_factory=list)
    account_id: int | None = None
    request_id: str | None = None
    retry_after: int | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        retry_after: int | None = None,
    ) -> "MondayAPIResponse":
        """Create from API response dictionary.

        :param data: Response dictionary from API.
        :param retry_after: Retry-After header value.
        :returns: MondayAPIResponse instance.
        """
        errors = [MondayError.from_dict(err) for err in data.get("errors", [])]

        request_id = None
        if errors:
            request_id = data.get("extensions", {}).get("request_id")

        return cls(
            data=data.get("data"),
            errors=errors,
            account_id=data.get("account_id"),
            request_id=request_id,
            retry_after=retry_after,
        )

    def has_errors(self) -> bool:
        """Check if response contains errors.

        :returns: True if errors exist.
        """
        return len(self.errors) > 0

    def get_error_codes(self) -> list[str]:
        """Get all error codes.

        :returns: List of error code strings.
        """
        return [error.extensions.code for error in self.errors]


class PaginationConfig(BaseModel):
    """Configuration for query pagination.

    :param enabled: Whether pagination is enabled.
    :param cursor_path: jq path to cursor (e.g., ".boards[].items_page.cursor").
    :param items_path: jq path to items (e.g., ".boards[].items_page.items").
    :param cursor_variable: Variable name for cursor in query.
    """

    enabled: bool = False
    cursor_path: str = ""
    items_path: str = ""
    cursor_variable: str = "cursor"

    model_config = {"frozen": True}


class DataType(StrEnum):
    """Supported data types for column mapping.

    Values:
        STRING: Text data, default type.
        INTEGER: Whole numbers (int64).
        FLOAT: Decimal numbers (float64).
        BOOLEAN: True/False values.
        DATETIME: Date and time with timezone.
        DATE: Date without time.
        JSON: Serialized JSON strings.

    Example::

        column_config = ColumnConfig(dtype=DataType.DATETIME)
    """

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    JSON = "json"


class OutputFormat(StrEnum):
    """Supported output file formats.

    Values:
        CSV: Comma-separated values, human-readable.
        JSON: JavaScript Object Notation, structured data.
        PARQUET: Columnar format, efficient for analytics.

    Example::

        writer = writer_factory.create(output_format=OutputFormat.CSV)
    """

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class EntityType(StrEnum):
    """Types of Monday.com entities that can be ingested.

    This enum enables scalable configuration for different entity types.
    Currently supports boards, with planned support for workspaces, users,
    and other Monday.com resources.

    Values:
        BOARD: Monday.com board with items and columns.
        WORKSPACE: Workspace containing multiple boards.
        USER: User account information.
        TEAM: Team/group of users.
        FOLDER: Folder containing boards.
        ITEM: Individual board item.
        COLUMN: Board column definition.

    Example::

        query_config = QueryConfig(
            name="get_workspace",
            entity_type=EntityType.WORKSPACE,
            graphql_file="get_workspace.graphql",
        )
    """

    BOARD = "board"
    WORKSPACE = "workspace"
    USER = "user"
    TEAM = "team"
    FOLDER = "folder"
    ITEM = "item"
    COLUMN = "column"


class ColumnConfig(BaseModel):
    """Type configuration for a DataFrame column.

    Defines how a column should be typed and validated during
    the transformation from API response to DataFrame.

    :param dtype: Target data type for the column.
    :param datetime_format: Format string for datetime parsing (optional).
    :param nullable: Whether null values are allowed in this column.

    Example::

        # String column that cannot be null
        id_config = ColumnConfig(dtype=DataType.STRING, nullable=False)

        # Datetime column with custom format
        date_config = ColumnConfig(
            dtype=DataType.DATETIME,
            datetime_format="%Y-%m-%dT%H:%M:%SZ",
            nullable=True,
        )
    """

    dtype: DataType = DataType.STRING
    datetime_format: str | None = None
    nullable: bool = True

    model_config = {"frozen": True}


class OutputFormat(StrEnum):
    """Supported output file formats."""

    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class TableConfig(BaseModel):
    """Configuration for transforming response to table using jq.

    Defines how API responses should be transformed into tabular
    data using jq expressions for filtering and reshaping.

    :param jq_transform: jq expression to transform and flatten data.
    :param columns: Column name to type configuration mapping.
    :param output_format: Default output format for this table.
    :param output_path: Default output file path prefix.

    Example::

        config = TableConfig.from_dict({
            "jq_transform": ".boards[].items_page.items[] | {id: .id, name: .name}",
            "columns": {
                "id": {"dtype": "string", "nullable": False},
                "name": {"dtype": "string", "nullable": True},
            },
            "output_format": "csv",
        })
    """

    jq_transform: str = ""
    columns: dict[str, ColumnConfig] = Field(default_factory=dict)
    output_format: OutputFormat = OutputFormat.PARQUET
    output_path: str = ""

    model_config = {"frozen": True}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TableConfig":
        """Create from dictionary.

        :param data: Dictionary with table settings.
        :returns: TableConfig instance.

        Example::

            config = TableConfig.from_dict({
                "jq_transform": ".items[]",
                "columns": {"id": "string"},
            })
        """
        # -----------------------------------------------------------------------
        # Parse column configurations from various input formats
        # -----------------------------------------------------------------------
        columns = {}
        for col_name, col_data in data.get("columns", {}).items():
            if isinstance(col_data, str):
                # Simple format: just a dtype string
                columns[col_name] = ColumnConfig(dtype=DataType(col_data))
            elif isinstance(col_data, dict):
                # Full format: dict with dtype and options
                dtype = DataType(col_data.get("dtype", "string"))
                columns[col_name] = ColumnConfig(
                    dtype=dtype,
                    datetime_format=col_data.get("datetime_format"),
                    nullable=col_data.get("nullable", True),
                )
            else:
                # Default to string type
                columns[col_name] = ColumnConfig()

        return cls(
            jq_transform=data.get("jq_transform", ""),
            columns=columns,
            output_format=OutputFormat(data.get("output_format", "parquet")),
            output_path=data.get("output_path", ""),
        )


class QueryConfig(BaseModel):
    """Configuration for a GraphQL query.

    Defines all settings for executing and processing a query, including
    pagination, variables, and output transformation.

    :param name: Query identifier used for lookup.
    :param description: Human-readable description.
    :param graphql_file: Filename of the .graphql file.
    :param entity_type: Type of entity being queried (board, workspace, etc.).
    :param pagination: Pagination configuration.
    :param variables: Default variables for the query.
    :param table: Table flattening configuration.

    Example::

        config = QueryConfig.from_dict(
            name="get_board_items",
            data={
                "description": "Fetch all items from boards",
                "entity_type": "board",
                "graphql_file": "get_board_items.graphql",
                "pagination": {"enabled": True},
            }
        )
    """

    name: str
    description: str = ""
    graphql_file: str
    entity_type: EntityType = EntityType.BOARD
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    variables: dict[str, Any] = Field(default_factory=dict)
    table: TableConfig | None = None

    model_config = {"frozen": True}

    @classmethod
    def from_dict(cls, *, name: str, data: dict[str, Any]) -> "QueryConfig":
        """Create from dictionary.

        :param name: Query name.
        :param data: Dictionary with query settings.
        :returns: QueryConfig instance.

        Example::

            config = QueryConfig.from_dict(
                name="get_users",
                data={"entity_type": "user", "graphql_file": "get_users.graphql"}
            )
        """
        # -----------------------------------------------------------------------
        # Parse pagination configuration
        # -----------------------------------------------------------------------
        pagination_data = data.get("pagination", {})

        # -----------------------------------------------------------------------
        # Parse table configuration if present
        # -----------------------------------------------------------------------
        table_data = data.get("table")
        table = TableConfig.from_dict(table_data) if table_data else None

        # -----------------------------------------------------------------------
        # Parse entity type with fallback to board
        # -----------------------------------------------------------------------
        entity_type_str = data.get("entity_type", "board")
        try:
            entity_type = EntityType(entity_type_str)
        except ValueError:
            entity_type = EntityType.BOARD

        return cls(
            name=name,
            description=data.get("description", ""),
            graphql_file=data.get("graphql_file", f"{name}.graphql"),
            entity_type=entity_type,
            pagination=PaginationConfig(**pagination_data),
            variables=data.get("variables", {}),
            table=table,
        )
