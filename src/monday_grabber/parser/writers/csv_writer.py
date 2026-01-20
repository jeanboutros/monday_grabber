"""CSV writer implementation."""

from pathlib import Path

import polars as pl

from .base import BaseWriter


class CsvWriter(BaseWriter):
    """Writes DataFrames to CSV files.

    Timestamps are formatted as ISO 8601 UTC strings.

    Example::

        writer = CsvWriter()
        path = writer.write(df=dataframe, path=Path("output/data"))
    """

    @property
    def extension(self) -> str:
        """Get file extension.

        :returns: CSV extension.
        """
        return ".csv"

    def write(self, *, df: pl.DataFrame, path: Path) -> Path:
        """Write DataFrame to CSV file.

        :param df: DataFrame to write.
        :param path: Output path.
        :returns: Path to written file.
        """
        path = path.with_suffix(self.extension)
        self._ensure_directory(path=path)

        # Format datetimes for text output
        df = self._format_datetimes(df=df)
        df.write_csv(path)

        return path
