# Science of Reading MCP Server — Docker Image
# Multi-stage build for a minimal, secure container

FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# ── Final stage ──────────────────────────────────────────────────────────────

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="Science of Reading MCP Server"
LABEL org.opencontainers.image.description="Evidence-based literacy analysis MCP server aligned to the Science of Reading"
LABEL org.opencontainers.image.source="https://github.com/kosburn0408/sor-mcp-server"

# Create non-root user with home /app
RUN groupadd -r sor && useradd -r -g sor -d /app -s /sbin/nologin sor

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /app/packages

# Copy application code
COPY --chown=sor:sor server.py .
COPY --chown=sor:sor webapp.py .
COPY --chown=sor:sor src/ ./src/
COPY --chown=sor:sor db/ ./db/
COPY --chown=sor:sor tests/ ./tests/

# Create data directory with proper permissions
RUN mkdir -p /data && chown sor:sor /data /app

# Set environment
ENV PYTHONPATH=/app/packages:.
ENV PATH="/app/packages/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV SOR_DB_PATH=/data/sor_evidence.duckdb

# Drop to non-root user
USER sor

# Health check — verifies DB and tools
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "from db.database import ensure_database; path, _ = ensure_database(); print(f'OK: {path}')" || exit 1

# Pre-seed the database during build
RUN python3 server.py --seed-only

EXPOSE 8080 8093

ENTRYPOINT ["python3", "server.py"]
CMD []
