"""YAML configuration loader."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from monday_grabber.core.types import QueryConfig


class ConfigLoader:
    """Loads and provides access to YAML configuration.

    :param config_path: Path to queries.yaml file.

    Example::

        config = ConfigLoader(config_path=Path("config/queries.yaml"))
        query_config = config.get_query_config(name="get_board_items")
        board_id = config.get_board_id(key="main_board")
    """

    def __init__(self, *, config_path: Path) -> None:
        self._config_path = config_path
        self._config: dict[str, Any] | None = None

    @property
    def config_path(self) -> Path:
        """Get configuration file path.

        :returns: Path to config file.
        """
        return self._config_path

    def load(self) -> dict[str, Any]:
        """Load configuration from file.

        :returns: Configuration dictionary.
        :raises FileNotFoundError: If config file not found.
        """
        if self._config is None:
            self._config = self._load_yaml()
        return self._config

    def reload(self) -> dict[str, Any]:
        """Force reload configuration from file.

        :returns: Configuration dictionary.
        :raises FileNotFoundError: If config file not found.
        """
        self._config = None
        self._get_query_config_cached.cache_clear()
        return self.load()

    def get_query_config(self, *, name: str) -> QueryConfig:
        """Get configuration for a query.

        :param name: Query name in config.
        :returns: Query configuration.
        :raises KeyError: If query not found.
        """
        return self._get_query_config_cached(name=name)

    @lru_cache(maxsize=64)
    def _get_query_config_cached(self, *, name: str) -> QueryConfig:
        """Cached query config lookup.

        :param name: Query name.
        :returns: Query configuration.
        :raises KeyError: If query not found.
        """
        config = self.load()
        queries = config.get("queries", {})

        if name not in queries:
            raise KeyError(f"Query '{name}' not found in configuration")

        return QueryConfig.from_dict(name=name, data=queries[name])

    def get_board_id(self, *, key: str) -> int:
        """Get a board ID by key.

        :param key: Board key in config.
        :returns: Board ID.
        :raises KeyError: If board not found.
        """
        config = self.load()
        boards = config.get("boards", {})

        if key not in boards:
            raise KeyError(f"Board '{key}' not found in configuration")

        return boards[key]["id"]

    def get_setting(self, *, key: str, default: Any = None) -> Any:
        """Get a setting value.

        :param key: Setting key.
        :param default: Default value if not found.
        :returns: Setting value.
        """
        config = self.load()
        return config.get("settings", {}).get(key, default)

    def get_all_query_names(self) -> list[str]:
        """Get all configured query names.

        :returns: List of query names.
        """
        config = self.load()
        return list(config.get("queries", {}).keys())

    def get_all_board_keys(self) -> list[str]:
        """Get all configured board keys.

        :returns: List of board keys.
        """
        config = self.load()
        return list(config.get("boards", {}).keys())

    def _load_yaml(self) -> dict[str, Any]:
        """Load YAML file.

        :returns: Parsed YAML as dictionary.
        :raises FileNotFoundError: If file not found.
        """
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self._config_path}")

        with open(self._config_path) as f:
            return yaml.safe_load(f)
