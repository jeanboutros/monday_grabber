"""HTTP client for Monday.com GraphQL API.

This module provides a low-level HTTP client for interacting with the
Monday.com GraphQL API. It handles authentication, request formatting,
and response parsing.

Example::

    from monday_grabber.client import MondayClient

    client = MondayClient(api_key="your_api_key")
    response = client.post(query="{ me { name } }")
    print(response.data)

Note:
    For higher-level operations with pagination support, use
    :class:`~monday_grabber.graphql.QueryExecutor` instead.
"""

from typing import Any

import requests

from monday_grabber.core.logging_config import get_logger
from monday_grabber.core.exceptions import MondayAPIResponse

from .response_handler import ResponseHandler

# ---------------------------------------------------------------------------
# Module logger
# ---------------------------------------------------------------------------
logger = get_logger("client.monday_client")


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

    DEFAULT_ENDPOINT = "https://api.monday.com/v2"

    def __init__(
        self,
        *,
        api_key: str,
        endpoint_url: str | None = None,
    ) -> None:
        logger.debug("Initializing MondayClient")

        # -----------------------------------------------------------------------
        # Validate that API key is provided
        # -----------------------------------------------------------------------
        if not api_key:
            logger.error("API key is required but not provided")
            raise ValueError("API key is required")

        # -----------------------------------------------------------------------
        # Store configuration
        # -----------------------------------------------------------------------
        self._api_key = api_key
        self._endpoint_url = endpoint_url or self.DEFAULT_ENDPOINT
        self._headers = self._create_headers()

        logger.info("MondayClient initialized with endpoint: %s", self._endpoint_url)

    def _create_headers(self) -> dict[str, str]:
        """Create authorization headers.

        :returns: Headers dictionary with Bearer token and content type.
        """
        # -----------------------------------------------------------------------
        # Create headers dict with authorization and content type
        # -----------------------------------------------------------------------
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    @property
    def endpoint_url(self) -> str:
        """Get endpoint URL.

        :returns: API endpoint URL.
        """
        return self._endpoint_url

    def post(
        self,
        *,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> MondayAPIResponse:
        """Execute a GraphQL query via HTTP POST.

        :param query: GraphQL query string.
        :param variables: Query variables.
        :returns: Parsed API response.
        :raises MondayAPIException: On API errors.
        :raises requests.RequestException: On network errors.
        """
        logger.debug("Executing GraphQL query")

        # -----------------------------------------------------------------------
        # Build request payload with query and optional variables
        # -----------------------------------------------------------------------
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
            logger.debug("Query variables: %s", list(variables.keys()))

        # -----------------------------------------------------------------------
        # Execute HTTP POST request to Monday.com API
        # -----------------------------------------------------------------------
        logger.debug("Sending POST request to %s", self._endpoint_url)
        response = requests.post(
            url=self._endpoint_url,
            headers=self._headers,
            json=payload,
        )
        logger.debug("Received response with status code: %d", response.status_code)

        # -----------------------------------------------------------------------
        # Parse and validate response through ResponseHandler
        # -----------------------------------------------------------------------
        return ResponseHandler.handle(response=response)

    def post_raw(
        self,
        *,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a GraphQL query and return raw data.

        :param query: GraphQL query string.
        :param variables: Query variables.
        :returns: Response data dictionary.
        :raises MondayAPIException: On API errors.
        :raises requests.RequestException: On network errors.
        """
        api_response = self.post(query=query, variables=variables)
        return api_response.data
