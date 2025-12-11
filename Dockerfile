# TickTick MCP Server Docker Image
# Multi-stage build for smaller final image

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy source
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Build wheel
RUN python -m build --wheel

# Runtime stage
FROM python:3.11-slim

LABEL org.opencontainers.image.title="TickTick MCP Server"
LABEL org.opencontainers.image.description="MCP server for TickTick task management"
LABEL org.opencontainers.image.source="https://github.com/MostafaSuliman/TickTick-MCP"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 ticktick

# Copy wheel from builder
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Create config directory
RUN mkdir -p /home/ticktick/.ticktick-mcp && chown -R ticktick:ticktick /home/ticktick

# Switch to non-root user
USER ticktick

# Set environment variables
ENV HOME=/home/ticktick
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from ticktick_mcp.server import create_server; create_server()" || exit 1

# Default command
ENTRYPOINT ["ticktick-mcp"]
