# ==============================================================================
# Monday Grabber - Multi-stage Docker Build
# ==============================================================================
# This Dockerfile creates a minimal production image for monday-grabber.
# It uses a multi-stage build to keep the final image small.
#
# Build:
#   docker build -t monday-grabber:latest .
#
# Run:
#   docker run --rm \
#     -e MONDAY_GRABBER__MONDAY_API_KEY=your_key \
#     -v $(pwd)/output:/app/output \
#     monday-grabber:latest \
#     --query get_board_items_wide --boards main_board
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder - Build the wheel package
# ------------------------------------------------------------------------------
FROM python:3.14-slim AS builder

# Install build dependencies
# ---------------------------------------------------------------------------
# We need these to build wheels for packages with native extensions (like jq)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjq-dev \
    libonig-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy project files needed for building
COPY pyproject.toml README.md ./
COPY src/ src/
COPY config/ config/

# Install pip and build tools
RUN pip install --no-cache-dir --upgrade pip build

# Build the wheel
# ---------------------------------------------------------------------------
# We build a wheel distribution which can be installed without build tools
# ---------------------------------------------------------------------------
RUN python -m build --wheel --outdir /build/dist


# ------------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ------------------------------------------------------------------------------
FROM python:3.14-slim AS runtime

# Security: Run as non-root user
# ---------------------------------------------------------------------------
# Create a dedicated user to run the application
# ---------------------------------------------------------------------------
RUN groupadd --gid 1000 grabber \
    && useradd --uid 1000 --gid grabber --shell /bin/bash --create-home grabber

# Install runtime dependencies only
# ---------------------------------------------------------------------------
# Only install libraries needed at runtime (not build tools)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjq1 \
    libonig5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy the wheel from builder stage
COPY --from=builder /build/dist/*.whl /tmp/

# Install the package from wheel
# ---------------------------------------------------------------------------
# Using pip to install the wheel keeps the image minimal (no uv overhead)
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm /tmp/*.whl

# Copy configuration files
COPY --chown=grabber:grabber config/ /app/config/

# Create output directory with correct permissions
RUN mkdir -p /app/output && chown grabber:grabber /app/output

# Switch to non-root user
USER grabber

# Set environment variables
# ---------------------------------------------------------------------------
# Default configuration - can be overridden at runtime
# ---------------------------------------------------------------------------
ENV MONDAY_GRABBER__LOG_LEVEL=INFO
ENV MONDAY_GRABBER__CONFIG_PATH=/app/config/queries.yaml
ENV MONDAY_GRABBER__OUTPUT_DIR=/app/output
ENV PYTHONUNBUFFERED=1

# Volume for output data
VOLUME ["/app/output"]

# Healthcheck - verify the CLI is accessible
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -m monday_grabber --list-queries || exit 1

# Default entrypoint runs the CLI
ENTRYPOINT ["python", "-m", "monday_grabber"]

# Default command shows help
CMD ["--help"]
