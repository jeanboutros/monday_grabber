"""Pagination handling for GraphQL queries."""

from typing import Any

from monday_grabber.core.types import PaginationConfig

from .response_parser import ResponseParser


class PaginationHandler:
    """Handles cursor-based pagination for GraphQL queries.

    Uses jq expressions for path navigation.

    :param config: Pagination configuration.

    Example::

        handler = PaginationHandler(config=pagination_config)
        cursor = handler.extract_cursor(data=response)
        if cursor:
            next_vars = handler.update_variables(
                variables=current_vars,
                cursor=cursor,
            )
    """

    def __init__(self, *, config: PaginationConfig) -> None:
        self._config = config

    @property
    def config(self) -> PaginationConfig:
        """Get pagination configuration.

        :returns: Pagination config.
        """
        return self._config

    @property
    def enabled(self) -> bool:
        """Check if pagination is enabled.

        :returns: True if enabled.
        """
        return self._config.enabled

    def extract_cursor(self, *, data: dict[str, Any]) -> str | None:
        """Extract pagination cursor from response.

        :param data: API response data.
        :returns: Cursor string, or None if no more pages.
        """
        path = ResponseParser.convert_path_to_jq(path=self._config.cursor_path)
        cursors = ResponseParser.get_all(data=data, path=path)
        for cursor in cursors:
            if cursor:
                return cursor
        return None

    def extract_items(self, *, data: dict[str, Any]) -> list[Any]:
        """Extract items from response.

        :param data: API response data.
        :returns: List of items.
        """
        path = ResponseParser.convert_path_to_jq(path=self._config.items_path)
        return ResponseParser.flatten(data=data, path=path)

    def update_variables(
        self,
        *,
        variables: dict[str, Any],
        cursor: str,
    ) -> dict[str, Any]:
        """Create new variables dict with updated cursor.

        :param variables: Current query variables.
        :param cursor: Next page cursor.
        :returns: New variables dict with cursor.
        """
        updated = variables.copy()
        updated[self._config.cursor_variable] = cursor
        return updated

    def merge_responses(
        self,
        *,
        responses: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Merge multiple paginated responses into one.

        :param responses: List of API responses.
        :returns: Merged response with all items.
        """
        if not responses:
            return {}

        if len(responses) == 1:
            return responses[0]

        result = ResponseParser.deep_copy(data=responses[0])

        all_items: list[Any] = []
        for response in responses:
            items = self.extract_items(data=response)
            all_items.extend(items)

        self._set_merged_items(data=result, items=all_items)
        self._clear_cursor(data=result)

        return result

    def _set_merged_items(
        self,
        *,
        data: dict[str, Any],
        items: list[Any],
    ) -> None:
        """Set merged items in response structure.

        :param data: Response data to modify.
        :param items: All collected items.
        """
        path = self._config.items_path
        keys = self._parse_path_keys(path=path)
        self._set_items_at_keys(data=data, keys=keys, items=items)

    def _parse_path_keys(self, *, path: str) -> list[str]:
        """Parse path into list of keys.

        :param path: Path like "boards[].items_page.items" or ".boards[].items_page.items".
        :returns: List of keys.
        """
        clean = path.lstrip(".")
        clean = clean.replace("[]", "")
        return clean.split(".")

    def _set_items_at_keys(
        self,
        *,
        data: dict[str, Any],
        keys: list[str],
        items: list[Any],
    ) -> None:
        """Traverse structure and set items at final key.

        :param data: Data structure to modify.
        :param keys: List of keys to traverse.
        :param items: Items to set.
        """
        current: Any = data
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                next_val = current[key]
                if isinstance(next_val, list) and next_val:
                    current = next_val[0]
                else:
                    current = next_val
            else:
                return

        if isinstance(current, dict) and keys:
            current[keys[-1]] = items

    def _clear_cursor(self, *, data: dict[str, Any]) -> None:
        """Clear cursor in merged response.

        :param data: Response data to modify.
        """
        path = self._config.cursor_path
        keys = self._parse_path_keys(path=path)

        if len(keys) < 2:
            return

        parent_keys = keys[:-1]
        current: Any = data

        for key in parent_keys:
            if isinstance(current, dict) and key in current:
                next_val = current[key]
                if isinstance(next_val, list) and next_val:
                    current = next_val[0]
                else:
                    current = next_val
            else:
                return

        if isinstance(current, dict) and "cursor" in current:
            current["cursor"] = None
