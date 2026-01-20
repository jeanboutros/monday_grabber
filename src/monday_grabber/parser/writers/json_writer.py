"""JSON writer implementation."""

from pathlib import Path

import polars as pl

from .base import BaseWriter


class JsonWriter(BaseWriter):
    """Writes DataFrames to JSON files.

    Timestamps are formatted as ISO 8601 UTC strings.
    Output is row-oriented JSON array.

    Example::

        writer = JsonWriter()
        path = writer.write(df=dataframe, path=Path("output/data"))
    """

    @property
    def extension(self) -> str:
        """Get file extension.

        :returns: JSON extension.
        """
        return ".json"

    def write(self, *, df: pl.DataFrame, path: Path) -> Path:
        """Write DataFrame to JSON file.

        :param df: DataFrame to write.
        :param path: Output path.
        :returns: Path to written file.
        """
        path = path.with_suffix(self.extension)
        self._ensure_directory(path=path)

        # Format datetimes for text output
        df = self._format_datetimes(df=df)

        # Write as JSON array
        df.write_json(path)

        return path
