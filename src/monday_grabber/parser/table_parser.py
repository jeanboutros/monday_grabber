"""Table parser for converting API responses to Polars DataFrames."""

import json
from typing import Any

import jq
import polars as pl

from monday_grabber.core.types import (
    DataType,
    TableConfig,
)


class TableParser:
    """Parses API responses into Polars DataFrames using jq.

    Uses a single jq expression to transform and flatten nested data.

    :param config: Table configuration with jq transform.

    Example::

        parser = TableParser(config=table_config)
        df = parser.parse(data=response_data)
    """

    def __init__(self, *, config: TableConfig) -> None:
        self._config = config

    @property
    def config(self) -> TableConfig:
        """Get table configuration.

        :returns: Table config.
        """
        return self._config

    def parse(self, *, data: dict[str, Any]) -> pl.DataFrame:
        """Parse API response to DataFrame using jq transform.

        :param data: API response data.
        :returns: Polars DataFrame with transformed data.
        :raises ValueError: If non-nullable column has null values.
        """
        rows = self._execute_transform(data=data)
        if not rows:
            return self._create_empty_dataframe()

        # Convert values for DataFrame compatibility
        converted_rows = [self._convert_row(row=row) for row in rows]

        # Create DataFrame with explicit schema to handle nullable columns
        schema = self._build_schema(sample_row=converted_rows[0])
        df = pl.DataFrame(converted_rows, schema=schema, strict=False)
        df = self._apply_types(df=df)

        # Validate non-nullable columns
        self._validate_nulls(df=df)

        return df

    def _validate_nulls(self, *, df: pl.DataFrame) -> None:
        """Validate that non-nullable columns have no null values.

        :param df: DataFrame to validate.
        :raises ValueError: If non-nullable column has null values.
        """
        for col_name, col_config in self._config.columns.items():
            if col_name not in df.columns:
                continue
            if not col_config.nullable:
                null_count = df[col_name].null_count()
                if null_count > 0:
                    raise ValueError(
                        f"Column '{col_name}' is not nullable but has {null_count} null values"
                    )

    def _build_schema(self, *, sample_row: dict[str, Any]) -> dict[str, pl.DataType]:
        """Build Polars schema from column config.

        Uses Utf8 for datetime/date since they need string parsing.

        :param sample_row: Sample row to get column names.
        :returns: Schema dictionary.
        """
        schema: dict[str, pl.DataType] = {}
        for col_name in sample_row.keys():
            if col_name in self._config.columns:
                dtype = self._config.columns[col_name].dtype
                # Use Utf8 for datetime/date - they'll be parsed in _apply_types
                if dtype in (DataType.DATETIME, DataType.DATE):
                    schema[col_name] = pl.Utf8
                else:
                    schema[col_name] = self._get_polars_type(dtype=dtype)
            else:
                schema[col_name] = pl.Utf8
        return schema

    def _execute_transform(self, *, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute jq transformation on data.

        :param data: API response data.
        :returns: List of transformed row dictionaries.
        """
        if not self._config.jq_transform:
            return [data] if isinstance(data, dict) else list(data)

        try:
            results = jq.compile(self._config.jq_transform).input(data).all()
            rows: list[dict[str, Any]] = []
            for result in results:
                if isinstance(result, dict):
                    rows.append(result)
                elif isinstance(result, list):
                    rows.extend(r for r in result if isinstance(r, dict))
            return rows
        except Exception as e:
            raise ValueError(f"jq transform failed: {e}") from e

    def _convert_row(self, *, row: dict[str, Any]) -> dict[str, Any]:
        """Convert row values for DataFrame compatibility.

        :param row: Raw row from jq transform.
        :returns: Row with converted values.
        """
        converted: dict[str, Any] = {}
        for key, value in row.items():
            if key in self._config.columns:
                dtype = self._config.columns[key].dtype
                converted[key] = self._convert_value(value=value, dtype=dtype)
            else:
                # Default: serialize complex types to JSON
                if isinstance(value, (dict, list)):
                    converted[key] = json.dumps(value, ensure_ascii=False)
                else:
                    converted[key] = value
        return converted

    def _convert_value(self, *, value: Any, dtype: DataType) -> Any:
        """Convert value to target type.

        :param value: Raw value.
        :param dtype: Target data type.
        :returns: Converted value.
        """
        if value is None:
            return None

        if dtype == DataType.JSON:
            if isinstance(value, str):
                return value
            return json.dumps(value, ensure_ascii=False)

        if dtype == DataType.STRING:
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            return str(value)

        if dtype == DataType.INTEGER:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        if dtype == DataType.FLOAT:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None

        if dtype == DataType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value) if value else None

        if dtype in (DataType.DATETIME, DataType.DATE):
            return str(value) if value else None

        return value

    def _apply_types(self, *, df: pl.DataFrame) -> pl.DataFrame:
        """Apply Polars types to DataFrame columns.

        :param df: DataFrame with raw data.
        :returns: DataFrame with correct types.
        """
        expressions: list[pl.Expr] = []

        for col_name, mapping in self._config.columns.items():
            if col_name not in df.columns:
                continue

            expr = self._get_type_expression(
                col_name=col_name,
                dtype=mapping.dtype,
                datetime_format=mapping.datetime_format,
            )
            expressions.append(expr)

        if expressions:
            return df.with_columns(expressions)
        return df

    def _get_type_expression(
        self,
        *,
        col_name: str,
        dtype: DataType,
        datetime_format: str | None = None,
    ) -> pl.Expr:
        """Get Polars expression for type conversion.

        :param col_name: Column name.
        :param dtype: Target data type.
        :param datetime_format: Format for datetime parsing.
        :returns: Polars expression.
        """
        col = pl.col(col_name)

        if dtype == DataType.INTEGER:
            return col.cast(pl.Int64, strict=False).alias(col_name)

        if dtype == DataType.FLOAT:
            return col.cast(pl.Float64, strict=False).alias(col_name)

        if dtype == DataType.BOOLEAN:
            return col.cast(pl.Boolean, strict=False).alias(col_name)

        if dtype == DataType.DATETIME:
            if datetime_format:
                return col.str.to_datetime(
                    format=datetime_format,
                    strict=False,
                    time_zone="UTC",
                ).alias(col_name)
            # Try multiple formats: ISO 8601 and Monday.com format
            # ISO 8601: "2024-01-15T10:30:00Z" (with T separator)
            # Monday.com: "2026-01-05 15:59:11 UTC" (space separator, UTC suffix)
            # First strip "Z" or " UTC" suffix, then parse
            normalized = (
                col.str.replace(" UTC$", "")
                .str.replace("Z$", "")
                .str.replace("T", " ")  # Normalize T to space
            )
            return normalized.str.to_datetime(
                format="%Y-%m-%d %H:%M:%S",
                strict=False,
                time_zone="UTC",
            ).alias(col_name)

        if dtype == DataType.DATE:
            if datetime_format:
                return col.str.to_date(
                    format=datetime_format,
                    strict=False,
                ).alias(col_name)
            return col.str.to_date(strict=False).alias(col_name)

        return col.cast(pl.Utf8, strict=False).alias(col_name)

    def _create_empty_dataframe(self) -> pl.DataFrame:
        """Create empty DataFrame with correct schema.

        :returns: Empty DataFrame.
        """
        schema: dict[str, pl.DataType] = {}
        for col_name, mapping in self._config.columns.items():
            schema[col_name] = self._get_polars_type(dtype=mapping.dtype)
        return pl.DataFrame(schema=schema)

    def _get_polars_type(self, *, dtype: DataType) -> pl.DataType:
        """Map DataType to Polars type.

        :param dtype: Our data type.
        :returns: Polars data type.
        """
        type_map: dict[DataType, type[pl.DataType]] = {
            DataType.STRING: pl.Utf8,
            DataType.INTEGER: pl.Int64,
            DataType.FLOAT: pl.Float64,
            DataType.BOOLEAN: pl.Boolean,
            DataType.DATETIME: pl.Datetime,
            DataType.DATE: pl.Date,
            DataType.JSON: pl.Utf8,
        }
        return type_map.get(dtype, pl.Utf8)
