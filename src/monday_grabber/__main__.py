"""Command-line entry point for Monday Grabber.

This module provides the CLI interface for ingesting data from Monday.com.
It supports fetching data from boards using configurable queries and
exporting to various file formats (CSV, JSON, Parquet).

Example usage::

    # Fetch a board using the wide format query
    python -m monday_grabber --query get_board_items_wide --boards main_board --format csv

    # Fetch multiple boards with debug logging
    python -m monday_grabber --query get_board_items --boards board1 board2 --format parquet --debug

    # List available queries and boards
    python -m monday_grabber --list-queries
    python -m monday_grabber --list-boards

Output files are named with timestamps::

    output/20260120T143052Z_get_board_items_wide_18310022893.csv

Attributes:
    PACKAGE_DIR: Path to the package directory.
    QUERIES_DIR: Path to GraphQL query files.
    CONFIG_DIR: Path to configuration files.
    OUTPUT_DIR: Path for output files.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import dotenv

# ---------------------------------------------------------------------------
# Import logging configuration first, before other module imports
# ---------------------------------------------------------------------------
from monday_grabber.core.logging_config import configure_logging, get_logger

# ---------------------------------------------------------------------------
# Import application modules
# ---------------------------------------------------------------------------
from monday_grabber.client import MondayClient
from monday_grabber.config import ConfigLoader
from monday_grabber.core import MondayAPIException, OutputFormat
from monday_grabber.graphql import QueryExecutor, QueryLoader
from monday_grabber.parser import TableParser, WriterFactory

# ---------------------------------------------------------------------------
# Module logger - obtained after imports to ensure proper configuration
# ---------------------------------------------------------------------------
logger = get_logger("__main__")

# ---------------------------------------------------------------------------
# Default paths - can be overridden via environment variables
# ---------------------------------------------------------------------------
PACKAGE_DIR = Path(__file__).parent
QUERIES_DIR = PACKAGE_DIR / "queries"

# Config and output directories can be set via environment variables (for Docker)
# or fall back to paths relative to the package
CONFIG_DIR = (
    Path(os.environ.get("MONDAY_GRABBER__CONFIG_PATH", "")).parent
    if os.environ.get("MONDAY_GRABBER__CONFIG_PATH")
    else PACKAGE_DIR.parent.parent / "config"
)
OUTPUT_DIR = (
    Path(os.environ.get("MONDAY_GRABBER__OUTPUT_DIR", ""))
    if os.environ.get("MONDAY_GRABBER__OUTPUT_DIR")
    else PACKAGE_DIR.parent.parent / "output"
)

# Default config file path
DEFAULT_CONFIG_PATH = (
    Path(os.environ.get("MONDAY_GRABBER__CONFIG_PATH", ""))
    if os.environ.get("MONDAY_GRABBER__CONFIG_PATH")
    else CONFIG_DIR / "queries.yaml"
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI.

    This function defines all command-line arguments accepted by the
    application. The parser supports query selection, board filtering,
    output format configuration, and various utility commands.

    :returns: Configured ArgumentParser instance.

    Example::

        parser = create_argument_parser()
        args = parser.parse_args()
    """
    # -----------------------------------------------------------------------
    # Create the main parser with description and epilog
    # -----------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        prog="monday_grabber",
        description=(
            "Ingest data from Monday.com boards and export to various formats. "
            "Supports flexible query configuration and multiple output formats."
        ),
        epilog=(
            "Examples:\n"
            "  %(prog)s --query get_board_items_wide --boards main_board\n"
            "  %(prog)s --query get_board_info --boards main_board --format json\n"
            "  %(prog)s --list-queries\n"
            "  %(prog)s --list-boards\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # -----------------------------------------------------------------------
    # Query and board selection arguments
    # -----------------------------------------------------------------------
    parser.add_argument(
        "-q",
        "--query",
        type=str,
        help="Name of the query to execute (e.g., get_board_items_wide)",
        metavar="QUERY_NAME",
    )

    parser.add_argument(
        "-b",
        "--boards",
        type=str,
        nargs="+",
        help="Board names to ingest (as defined in config/queries.yaml)",
        metavar="BOARD",
    )

    # -----------------------------------------------------------------------
    # Output configuration arguments
    # -----------------------------------------------------------------------
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["csv", "json", "parquet"],
        default="csv",
        help="Output file format (default: csv)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help=f"Output directory (default: {OUTPUT_DIR})",
        metavar="DIR",
    )

    # -----------------------------------------------------------------------
    # Utility commands
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--list-queries",
        action="store_true",
        help="List all available query names and exit",
    )

    parser.add_argument(
        "--list-boards",
        action="store_true",
        help="List all configured boards and exit",
    )

    # -----------------------------------------------------------------------
    # Logging configuration
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging for verbose output",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )

    # -----------------------------------------------------------------------
    # Configuration overrides
    # -----------------------------------------------------------------------
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help=f"Path to queries.yaml config file (default: {DEFAULT_CONFIG_PATH})",
        metavar="FILE",
    )

    return parser


def generate_output_filename(
    *,
    query_name: str,
    entity_id: int | str,
    file_format: str,
) -> str:
    """Generate a timestamped output filename.

    Creates a filename following the pattern:
    YYYYMMDDTHHMMSSZ_<query_name>_<entity_id>.<file_format>

    :param query_name: Name of the query that was executed.
    :param entity_id: ID of the entity (board, workspace, etc.).
    :param file_format: File extension without dot (csv, json, parquet).
    :returns: Generated filename string.

    Example::

        filename = generate_output_filename(
            query_name="get_board_items_wide",
            entity_id=18310022893,
            file_format="csv",
        )
        # Returns: "20260120T143052Z_get_board_items_wide_18310022893.csv"
    """
    # -----------------------------------------------------------------------
    # Generate UTC timestamp in compact ISO format
    # -----------------------------------------------------------------------
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # -----------------------------------------------------------------------
    # Construct the filename with all components
    # -----------------------------------------------------------------------
    filename = f"{timestamp}_{query_name}_{entity_id}.{file_format}"

    logger.debug("Generated output filename: %s", filename)
    return filename


def list_available_queries(config_loader: ConfigLoader) -> None:
    """Display all available query names from the configuration.

    :param config_loader: Configuration loader instance.

    Example::

        list_available_queries(config_loader)
        # Output:
        # Available queries:
        #   - get_board_items
        #   - get_board_items_wide
        #   - get_board_info
    """
    logger.info("Listing available queries")

    query_names = config_loader.get_all_query_names()

    if not query_names:
        logger.warning("No queries defined in configuration")
        return

    # -----------------------------------------------------------------------
    # Print formatted list of queries
    # -----------------------------------------------------------------------
    print("\nAvailable queries:")
    for name in sorted(query_names):
        print(f"  - {name}")
    print()


def list_available_boards(config_loader: ConfigLoader) -> None:
    """Display all configured boards from the configuration.

    :param config_loader: Configuration loader instance.

    Example::

        list_available_boards(config_loader)
        # Output:
        # Configured boards:
        #   - main_board (ID: 18310022893)
    """
    logger.info("Listing configured boards")

    board_keys = config_loader.get_all_board_keys()

    if not board_keys:
        logger.warning("No boards defined in configuration")
        return

    # -----------------------------------------------------------------------
    # Print formatted list of boards with their IDs
    # -----------------------------------------------------------------------
    print("\nConfigured boards:")
    for key in sorted(board_keys):
        try:
            board_id = config_loader.get_board_id(key=key)
            print(f"  - {key} (ID: {board_id})")
        except KeyError:
            print(f"  - {key} (ID: not configured)")
    print()


def initialize_components(
    *,
    api_key: str,
    config_path: Path,
) -> tuple[QueryExecutor, ConfigLoader, WriterFactory]:
    """Initialize all application components.

    Creates and configures the client, query executor, config loader,
    and writer factory needed for data ingestion.

    :param api_key: Monday.com API key.
    :param config_path: Path to the configuration file.
    :returns: Tuple of (QueryExecutor, ConfigLoader, WriterFactory).
    :raises FileNotFoundError: If config file doesn't exist.

    Example::

        executor, config_loader, writer_factory = initialize_components(
            api_key="my_api_key",
            config_path=Path("config/queries.yaml"),
        )
    """
    logger.info("Initializing application components")

    # -----------------------------------------------------------------------
    # Validate configuration file exists
    # -----------------------------------------------------------------------
    if not config_path.exists():
        logger.error("Configuration file not found: %s", config_path)
        raise FileNotFoundError(
            f"YAML config file for the queries not found: {config_path}"
        )

    # -----------------------------------------------------------------------
    # Create Monday.com API client
    # -----------------------------------------------------------------------
    logger.debug("Creating MondayClient")
    client = MondayClient(api_key=api_key)

    # -----------------------------------------------------------------------
    # Create query loader for GraphQL files
    # -----------------------------------------------------------------------
    logger.debug("Creating QueryLoader with queries_dir=%s", QUERIES_DIR)
    query_loader = QueryLoader(queries_dir=QUERIES_DIR)

    # -----------------------------------------------------------------------
    # Create configuration loader
    # -----------------------------------------------------------------------
    logger.debug("Creating ConfigLoader with config_path=%s", config_path)
    config_loader = ConfigLoader(config_path=config_path)

    # -----------------------------------------------------------------------
    # Create query executor with all dependencies
    # -----------------------------------------------------------------------
    logger.debug("Creating QueryExecutor")
    executor = QueryExecutor(
        client=client,
        query_loader=query_loader,
        config_loader=config_loader,
    )

    # -----------------------------------------------------------------------
    # Create writer factory for output
    # -----------------------------------------------------------------------
    logger.debug("Creating WriterFactory")
    writer_factory = WriterFactory()

    logger.info("All components initialized successfully")
    return executor, config_loader, writer_factory


def ingest_board(
    *,
    executor: QueryExecutor,
    config_loader: ConfigLoader,
    writer_factory: WriterFactory,
    query_name: str,
    board_key: str,
    output_format: OutputFormat,
    output_dir: Path,
) -> Path | None:
    """Ingest data from a single board and write to file.

    Executes the specified query against the board, transforms the
    response using the configured jq transform, and writes the result
    to a timestamped output file.

    :param executor: Query executor instance.
    :param config_loader: Configuration loader instance.
    :param writer_factory: Writer factory instance.
    :param query_name: Name of the query to execute.
    :param board_key: Board key as defined in configuration.
    :param output_format: Output file format.
    :param output_dir: Directory for output files.
    :returns: Path to written file, or None if no data.
    :raises KeyError: If board_key is not found in configuration.
    :raises MondayAPIException: If API request fails.

    Example::

        path = ingest_board(
            executor=executor,
            config_loader=config_loader,
            writer_factory=writer_factory,
            query_name="get_board_items_wide",
            board_key="main_board",
            output_format=OutputFormat.CSV,
            output_dir=Path("output"),
        )
    """
    logger.info(
        "Starting ingestion for board: %s with query: %s", board_key, query_name
    )

    # -----------------------------------------------------------------------
    # Get board ID from configuration
    # -----------------------------------------------------------------------
    board_id = config_loader.get_board_id(key=board_key)
    logger.debug("Resolved board_key=%s to board_id=%s", board_key, board_id)

    # -----------------------------------------------------------------------
    # Get query configuration for table transformation
    # -----------------------------------------------------------------------
    query_config = config_loader.get_query_config(name=query_name)
    logger.debug("Loaded query configuration for: %s", query_name)

    # -----------------------------------------------------------------------
    # Execute the query against the Monday.com API
    # -----------------------------------------------------------------------
    logger.info("Executing query: %s for board_id: %s", query_name, board_id)
    response = executor.execute_configured(
        query_name=query_name,
        target_board_ids=[board_id],
    )

    # -----------------------------------------------------------------------
    # Handle empty response
    # -----------------------------------------------------------------------
    if not response:
        logger.warning("No data returned for board_id=%s", board_id)
        return None

    # -----------------------------------------------------------------------
    # Verify table configuration exists for transformation
    # -----------------------------------------------------------------------
    if not query_config.table:
        logger.error("No table configuration defined for query: %s", query_name)
        raise ValueError(f"No table config defined for query: {query_name}")

    # -----------------------------------------------------------------------
    # Parse response to DataFrame using jq transform
    # -----------------------------------------------------------------------
    logger.debug("Parsing response with jq transform")
    parser = TableParser(config=query_config.table)
    df = parser.parse(data=response)
    logger.info("Parsed %d rows from response", len(df))

    # -----------------------------------------------------------------------
    # Generate timestamped output filename
    # -----------------------------------------------------------------------
    filename = generate_output_filename(
        query_name=query_name,
        entity_id=board_id,
        file_format=output_format.value,
    )
    output_path = output_dir / filename

    # -----------------------------------------------------------------------
    # Write DataFrame to file using appropriate writer
    # -----------------------------------------------------------------------
    logger.debug("Creating writer for format: %s", output_format.value)
    writer = writer_factory.create(output_format=output_format)
    written_path = writer.write(df=df, path=output_path)

    logger.info("Successfully wrote %d rows to: %s", len(df), written_path)
    return written_path


def run_ingestion(args: argparse.Namespace) -> int:
    """Run the main ingestion workflow.

    This function orchestrates the entire ingestion process: loading
    configuration, initializing components, and processing each board.

    :param args: Parsed command-line arguments.
    :returns: Exit code (0 for success, 1 for failure).

    Example::

        parser = create_argument_parser()
        args = parser.parse_args()
        exit_code = run_ingestion(args)
    """
    logger.info("Starting ingestion workflow")

    # -----------------------------------------------------------------------
    # Load environment variables from .env file
    # -----------------------------------------------------------------------
    logger.debug("Loading environment variables from .env")
    dotenv.load_dotenv()

    # -----------------------------------------------------------------------
    # Validate API key is available
    # -----------------------------------------------------------------------
    api_key = os.getenv("MONDAY_GRABBER__MONDAY_API_KEY")
    if not api_key:
        logger.error("MONDAY_GRABBER__MONDAY_API_KEY environment variable not set")
        print(
            "Error: MONDAY_GRABBER__MONDAY_API_KEY not set. "
            "Please set it in your environment or .env file.",
            file=sys.stderr,
        )
        return 1

    # -----------------------------------------------------------------------
    # Determine configuration file path
    # -----------------------------------------------------------------------
    config_path = Path(args.config) if args.config else DEFAULT_CONFIG_PATH
    logger.debug("Using configuration file: %s", config_path)

    # -----------------------------------------------------------------------
    # Initialize all components
    # -----------------------------------------------------------------------
    try:
        executor, config_loader, writer_factory = initialize_components(
            api_key=api_key,
            config_path=config_path,
        )
    except FileNotFoundError as e:
        logger.error("Configuration error: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # -----------------------------------------------------------------------
    # Handle utility commands (list queries/boards)
    # -----------------------------------------------------------------------
    if args.list_queries:
        list_available_queries(config_loader)
        return 0

    if args.list_boards:
        list_available_boards(config_loader)
        return 0

    # -----------------------------------------------------------------------
    # Validate required arguments for ingestion
    # -----------------------------------------------------------------------
    if not args.query:
        logger.error("No query specified")
        print(
            "Error: --query is required. Use --list-queries to see available queries.",
            file=sys.stderr,
        )
        return 1

    # -----------------------------------------------------------------------
    # Determine boards to process
    # -----------------------------------------------------------------------
    if args.boards:
        board_keys = args.boards
    else:
        # Default to all configured boards
        board_keys = config_loader.get_all_board_keys()
        if not board_keys:
            logger.error("No boards specified and none configured in YAML")
            print(
                "Error: No boards specified and none configured. Use --list-boards to see options.",
                file=sys.stderr,
            )
            return 1

    logger.info("Processing %d board(s): %s", len(board_keys), board_keys)

    # -----------------------------------------------------------------------
    # Determine output format and directory
    # -----------------------------------------------------------------------
    output_format = OutputFormat(args.format)
    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(
        "Output format: %s, Output directory: %s", output_format.value, output_dir
    )

    # -----------------------------------------------------------------------
    # Process each board
    # -----------------------------------------------------------------------
    success_count = 0
    error_count = 0

    for board_key in board_keys:
        try:
            result_path = ingest_board(
                executor=executor,
                config_loader=config_loader,
                writer_factory=writer_factory,
                query_name=args.query,
                board_key=board_key,
                output_format=output_format,
                output_dir=output_dir,
            )

            if result_path:
                print(f"✓ {board_key}: {result_path}")
                success_count += 1
            else:
                print(f"⚠ {board_key}: No data returned")

        except KeyError as e:
            logger.error("Board not found: %s - %s", board_key, e)
            print(f"✗ {board_key}: Board not found in configuration", file=sys.stderr)
            error_count += 1

        except MondayAPIException as e:
            logger.error("API error for board %s: %s", board_key, e)
            print(f"✗ {board_key}: API error - {e}", file=sys.stderr)
            if e.retry_after:
                logger.info("Retry after %d seconds", e.retry_after)
            error_count += 1

        except Exception as e:
            logger.exception("Unexpected error processing board %s", board_key)
            print(f"✗ {board_key}: Unexpected error - {e}", file=sys.stderr)
            error_count += 1

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    logger.info(
        "Ingestion complete: %d succeeded, %d failed", success_count, error_count
    )
    print(f"\nSummary: {success_count} succeeded, {error_count} failed")

    return 1 if error_count > 0 else 0


def main() -> None:
    """Main entry point for the Monday Grabber CLI.

    This function sets up argument parsing, configures logging based on
    command-line flags, and runs the ingestion workflow.

    Exit codes:
        0: Success
        1: Error (configuration, API, or processing error)

    Example::

        # Run from command line
        python -m monday_grabber --query get_board_items_wide --boards main_board

        # Or programmatically
        from monday_grabber.__main__ import main
        main()
    """
    # -----------------------------------------------------------------------
    # Parse command-line arguments
    # -----------------------------------------------------------------------
    parser = create_argument_parser()
    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Configure logging based on command-line flags
    # Priority: CLI args > env vars > defaults
    # -----------------------------------------------------------------------
    if args.debug:
        log_level = "DEBUG"
    elif args.quiet:
        log_level = "ERROR"
    else:
        # None allows configure_logging to check env var or use default
        log_level = None

    configure_logging(level=log_level)
    logger.debug("Logging configured with level: %s", log_level or "from env/default")

    # -----------------------------------------------------------------------
    # Run the main workflow
    # -----------------------------------------------------------------------
    exit_code = run_ingestion(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
