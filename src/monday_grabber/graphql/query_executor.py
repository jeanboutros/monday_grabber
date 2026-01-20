"""GraphQL query executor with pagination support."""

import logging
from typing import Any

from monday_grabber.client import MondayClient
from monday_grabber.config import ConfigLoader
from monday_grabber.core.types import PaginationConfig, QueryConfig

from .pagination import PaginationHandler
from .query_loader import QueryLoader


logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes GraphQL queries with configuration and pagination support.

    Orchestrates query loading, execution, and pagination handling.

    :param client: Monday.com HTTP client.
    :param query_loader: Query file loader.
    :param config_loader: Configuration loader (optional).

    Example::

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

    def __init__(
        self,
        *,
        client: MondayClient,
        query_loader: QueryLoader,
        config_loader: ConfigLoader | None = None,
    ) -> None:
        self._client = client
        self._query_loader = query_loader
        self._config_loader = config_loader

    def execute(
        self,
        *,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query.

        :param query: GraphQL query string.
        :param variables: Query variables.
        :returns: Response data.
        :raises MondayAPIException: On API errors.
        """
        return self._client.post_raw(query=query, variables=variables)

    def execute_paginated(
        self,
        *,
        query: str,
        variables: dict[str, Any],
        pagination_config: PaginationConfig,
        max_pages: int | None = None,
    ) -> dict[str, Any]:
        """Execute a paginated query, fetching all pages.

        :param query: GraphQL query string.
        :param variables: Query variables.
        :param pagination_config: Pagination settings.
        :param max_pages: Maximum pages to fetch (None for unlimited).
        :returns: Merged response data.
        :raises MondayAPIException: On API errors.
        """
        if not pagination_config.enabled:
            return self.execute(query=query, variables=variables)

        handler = PaginationHandler(config=pagination_config)
        responses: list[dict[str, Any]] = []
        current_vars = variables.copy()
        page_count = 0

        while True:
            page_count += 1
            logger.info("Fetching page %d...", page_count)

            response = self.execute(query=query, variables=current_vars)
            responses.append(response)

            cursor = handler.extract_cursor(data=response)

            if not cursor:
                logger.info("No more pages. Total: %d", page_count)
                break

            if max_pages and page_count >= max_pages:
                logger.info("Reached max pages: %d", max_pages)
                break

            current_vars = handler.update_variables(
                variables=current_vars,
                cursor=cursor,
            )

        return handler.merge_responses(responses=responses)

    def execute_configured(
        self,
        *,
        query_name: str,
        max_pages: int | None = None,
        **variable_overrides: Any,
    ) -> dict[str, Any]:
        """Execute a query using YAML configuration.

        :param query_name: Query name in config file.
        :param max_pages: Maximum pages for pagination.
        :param variable_overrides: Override default variables.
        :returns: Response data (merged if paginated).
        :raises MondayAPIException: On API errors.
        :raises KeyError: If query not in config.
        :raises FileNotFoundError: If query file not found.
        """
        if self._config_loader is None:
            raise ValueError("ConfigLoader required for configured queries")

        config = self._config_loader.get_query_config(name=query_name)
        query = self._query_loader.get_query_for_config(config=config)
        variables = {**config.variables, **variable_overrides}

        if config.pagination.enabled:
            return self.execute_paginated(
                query=query,
                variables=variables,
                pagination_config=config.pagination,
                max_pages=max_pages,
            )
        else:
            return self.execute(query=query, variables=variables)

    def execute_with_config(
        self,
        *,
        config: QueryConfig,
        max_pages: int | None = None,
        **variable_overrides: Any,
    ) -> dict[str, Any]:
        """Execute a query with explicit QueryConfig.

        :param config: Query configuration.
        :param max_pages: Maximum pages for pagination.
        :param variable_overrides: Override default variables.
        :returns: Response data.
        :raises MondayAPIException: On API errors.
        """
        query = self._query_loader.get_query_for_config(config=config)
        variables = {**config.variables, **variable_overrides}

        if config.pagination.enabled:
            return self.execute_paginated(
                query=query,
                variables=variables,
                pagination_config=config.pagination,
                max_pages=max_pages,
            )
        else:
            return self.execute(query=query, variables=variables)
