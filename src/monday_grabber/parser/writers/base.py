"""Base writer with shared datetime formatting logic."""

from pathlib import Path

import polars as pl


class BaseWriter:
    """Base class for writers with shared formatting logic.

    Provides datetime formatting to ISO 8601 UTC for text-based formats.
    """

    def _ensure_directory(self, *, path: Path) -> None:
        """Create parent directories if needed.

        :param path: File path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

    def _format_datetimes(self, *, df: pl.DataFrame) -> pl.DataFrame:
        """Convert datetime columns to ISO 8601 UTC strings.

        :param df: DataFrame to process.
        :returns: DataFrame with formatted datetime columns.
        """
        expressions: list[pl.Expr] = []
        for col_name, dtype in df.schema.items():
            if isinstance(dtype, pl.Datetime):
                expr = (
                    pl.col(col_name)
                    .dt.convert_time_zone("UTC")
                    .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    .alias(col_name)
                )
                expressions.append(expr)
            elif dtype == pl.Date:
                expr = pl.col(col_name).dt.strftime("%Y-%m-%d").alias(col_name)
                expressions.append(expr)

        if expressions:
            return df.with_columns(expressions)
        return df
