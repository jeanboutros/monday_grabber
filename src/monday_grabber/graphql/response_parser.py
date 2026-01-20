"""GraphQL response parsing using jq."""

from typing import Any
import copy

import jq


class ResponseParser:
    """Parses nested GraphQL responses using jq expressions.

    Uses jq syntax for path expressions, which is more powerful
    and standardized than custom path notation.

    Example::

        parser = ResponseParser()
        cursor = parser.get_first(
            data=response,
            path=".boards[].items_page.cursor",
        )
    """

    @classmethod
    def query(cls, *, data: dict[str, Any], path: str) -> list[Any]:
        """Execute jq query and return all results.

        :param data: Dictionary to query.
        :param path: jq expression (e.g., ".boards[].items_page.cursor").
        :returns: List of all matching values.
        """
        try:
            return jq.compile(path).input(data).all()
        except Exception:
            return []

    @classmethod
    def get_first(cls, *, data: dict[str, Any], path: str) -> Any:
        """Get first matching value from jq query.

        :param data: Dictionary to query.
        :param path: jq expression.
        :returns: First matching value, or None if not found.
        """
        results = cls.query(data=data, path=path)
        return results[0] if results else None

    @classmethod
    def get_all(cls, *, data: dict[str, Any], path: str) -> list[Any]:
        """Get all matching values from jq query.

        :param data: Dictionary to query.
        :param path: jq expression.
        :returns: List of all matching values.
        """
        return cls.query(data=data, path=path)

    @classmethod
    def flatten(cls, *, data: dict[str, Any], path: str) -> list[Any]:
        """Get all values and flatten nested arrays.

        :param data: Dictionary to query.
        :param path: jq expression.
        :returns: Flattened list of items.
        """
        results = cls.query(data=data, path=path)
        flattened: list[Any] = []
        for item in results:
            if isinstance(item, list):
                flattened.extend(item)
            elif item is not None:
                flattened.append(item)
        return flattened

    @classmethod
    def deep_copy(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """Create a deep copy of data.

        :param data: Dictionary to copy.
        :returns: Deep copy.
        """
        return copy.deepcopy(data)

    @classmethod
    def set_at_path(
        cls,
        *,
        data: dict[str, Any],
        keys: list[str],
        value: Any,
    ) -> None:
        """Set a value at a path specified by keys.

        :param data: Dictionary to modify.
        :param keys: List of keys to traverse.
        :param value: Value to set.
        """
        current = data
        for key in keys[:-1]:
            if key in current:
                current = current[key]
            else:
                return
        if keys:
            current[keys[-1]] = value

    @classmethod
    def convert_path_to_jq(cls, *, path: str) -> str:
        """Convert old-style path to jq syntax.

        :param path: Path like "boards[].items_page.cursor".
        :returns: jq path like ".boards[].items_page.cursor".
        """
        if not path.startswith("."):
            return f".{path}"
        return path
