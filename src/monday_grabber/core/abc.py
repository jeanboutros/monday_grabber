"""Abstract base classes and protocols for dependency injection."""

from typing import Any, Protocol

from .types import QueryConfig


class HttpClient(Protocol):
    """Protocol for HTTP client implementations.

    Defines the interface for making HTTP requests to GraphQL endpoints.
    """

    def post(
        self,
        *,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query via HTTP POST.

        :param query: GraphQL query string.
        :param variables: Query variables.
        :returns: Raw JSON response as dictionary.
        :raises requests.RequestException: On network errors.
        """
        ...


class QueryProvider(Protocol):
    """Protocol for query loading implementations.

    Defines the interface for loading GraphQL queries and their configurations.
    """

    def get_query(self, *, name: str) -> str:
        """Load a GraphQL query by name.

        :param name: Query name or filename.
        :returns: Query string.
        :raises FileNotFoundError: If query file not found.
        """
        ...

    def get_config(self, *, name: str) -> QueryConfig:
        """Get configuration for a query.

        :param name: Query name.
        :returns: Query configuration.
        :raises KeyError: If query not in config.
        """
        ...


class ConfigProvider(Protocol):
    """Protocol for configuration loading implementations.

    Defines the interface for accessing application configuration.
    """

    def get_setting(self, *, key: str, default: Any = None) -> Any:
        """Get a configuration setting.

        :param key: Setting key.
        :param default: Default value if not found.
        :returns: Setting value.
        """
        ...

    def get_board_id(self, *, key: str) -> int:
        """Get a board ID by key.

        :param key: Board key in config.
        :returns: Board ID.
        :raises KeyError: If board not found.
        """
        ...
