"""Parquet writer implementation."""

from pathlib import Path

import polars as pl

from .base import BaseWriter


class ParquetWriter(BaseWriter):
    """Writes DataFrames to Parquet files.

    Parquet preserves native datetime types with timezone information.

    Example::

        writer = ParquetWriter()
        path = writer.write(df=dataframe, path=Path("output/data"))
    """

    @property
    def extension(self) -> str:
        """Get file extension.

        :returns: Parquet extension.
        """
        return ".parquet"

    def write(self, *, df: pl.DataFrame, path: Path) -> Path:
        """Write DataFrame to Parquet file.

        :param df: DataFrame to write.
        :param path: Output path.
        :returns: Path to written file.
        """
        path = path.with_suffix(self.extension)
        self._ensure_directory(path=path)

        # Parquet preserves native types, no datetime formatting needed
        df.write_parquet(path)

        return path
