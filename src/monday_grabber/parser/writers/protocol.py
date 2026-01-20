"""Protocol for DataFrame writers."""

from pathlib import Path
from typing import Protocol

import polars as pl


class DataFrameWriter(Protocol):
    """Protocol for writing DataFrames to files.

    Implementations handle specific file formats (CSV, JSON, Parquet, etc.).
    Each writer is responsible for its own format-specific logic.
    """

    @property
    def extension(self) -> str:
        """File extension for this writer (e.g., '.csv').

        :returns: File extension with leading dot.
        """
        ...

    def write(self, *, df: pl.DataFrame, path: Path) -> Path:
        """Write DataFrame to file.

        :param df: DataFrame to write.
        :param path: Output path (extension may be adjusted).
        :returns: Path to written file.
        """
        ...
