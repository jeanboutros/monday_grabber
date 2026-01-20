"""GraphQL query file loader."""

from functools import lru_cache
from pathlib import Path

from monday_grabber.core.types import QueryConfig


class QueryLoader:
    """Loads GraphQL query files from disk.

    :param queries_dir: Directory containing .graphql files.

    Example::

        loader = QueryLoader(queries_dir=Path("./queries"))
        query = loader.get_query(name="get_board_items")
    """

    def __init__(self, *, queries_dir: Path) -> None:
        self._queries_dir = queries_dir

    @property
    def queries_dir(self) -> Path:
        """Get queries directory path.

        :returns: Path to queries directory.
        """
        return self._queries_dir

    def get_query(self, *, name: str) -> str:
        """Load a GraphQL query by name.

        :param name: Query filename (with or without .graphql extension).
        :returns: Query string.
        :raises FileNotFoundError: If query file not found.
        """
        return self._load_file(name=name)

    @lru_cache(maxsize=128)
    def _load_file(self, *, name: str) -> str:
        """Load and cache query file contents.

        :param name: Query filename.
        :returns: File contents.
        :raises FileNotFoundError: If file not found.
        """
        filename = name if name.endswith(".graphql") else f"{name}.graphql"
        path = self._queries_dir / filename

        if not path.exists():
            raise FileNotFoundError(f"Query file not found: {path}")

        return path.read_text()

    def get_query_for_config(self, *, config: QueryConfig) -> str:
        """Load query for a QueryConfig.

        :param config: Query configuration.
        :returns: Query string.
        :raises FileNotFoundError: If query file not found.
        """
        return self.get_query(name=config.graphql_file)

    def clear_cache(self) -> None:
        """Clear the query file cache."""
        self._load_file.cache_clear()
