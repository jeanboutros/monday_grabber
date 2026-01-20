"""Factory for creating DataFrame writers."""

from pathlib import Path

from monday_grabber.core.types import OutputFormat

from .protocol import DataFrameWriter
from .csv_writer import CsvWriter
from .json_writer import JsonWriter
from .parquet_writer import ParquetWriter


class WriterFactory:
    """Factory for creating DataFrame writers.

    Uses dependency injection to provide the correct writer
    based on the requested output format.

    Example::

        factory = WriterFactory()
        writer = factory.create(output_format=OutputFormat.CSV)
        path = writer.write(df=dataframe, path=Path("output/data"))
    """

    _writers: dict[OutputFormat, type[DataFrameWriter]] = {
        OutputFormat.CSV: CsvWriter,
        OutputFormat.JSON: JsonWriter,
        OutputFormat.PARQUET: ParquetWriter,
    }

    def create(
        self,
        *,
        output_format: OutputFormat | None = None,
        path: Path | None = None,
    ) -> DataFrameWriter:
        """Create a writer for the specified format.

        :param output_format: Desired output format.
        :param path: File path (used to infer format if not specified).
        :returns: Writer instance.
        :raises ValueError: If format cannot be determined.
        """
        if output_format is None:
            if path is None:
                raise ValueError("Either output_format or path must be provided")
            output_format = self._infer_format(path=path)

        writer_class = self._writers.get(output_format)
        if writer_class is None:
            raise ValueError(f"No writer registered for format: {output_format}")

        return writer_class()

    def _infer_format(self, *, path: Path) -> OutputFormat:
        """Infer format from file extension.

        :param path: File path.
        :returns: Output format.
        """
        suffix = path.suffix.lower()
        format_map = {
            ".csv": OutputFormat.CSV,
            ".json": OutputFormat.JSON,
            ".parquet": OutputFormat.PARQUET,
        }
        return format_map.get(suffix, OutputFormat.PARQUET)

    def register(
        self,
        *,
        output_format: OutputFormat,
        writer_class: type[DataFrameWriter],
    ) -> None:
        """Register a custom writer for a format.

        :param output_format: Format to register for.
        :param writer_class: Writer class to use.
        """
        self._writers[output_format] = writer_class
