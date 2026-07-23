"""Database connection management for the Science of Reading MCP server."""

import duckdb
import os
from pathlib import Path
from typing import Optional

DB_DIR = Path(__file__).parent
DEFAULT_DB_PATH = str(DB_DIR / "sor_evidence.duckdb")
SCHEMA_PATH = DB_DIR / "schema.sql"

_connection: Optional[duckdb.DuckDBPyConnection] = None


def get_db_path() -> str:
    """Get database path from environment or default."""
    return os.environ.get("SOR_DB_PATH", DEFAULT_DB_PATH)


def get_connection(read_only: bool = True) -> duckdb.DuckDBPyConnection:
    """Get or create a DuckDB connection. Uses in-memory read-only mode by default for analytical queries.

    The connection is shared across tools — DuckDB handles concurrent reads efficiently.
    """
    global _connection
    if _connection is not None:
        return _connection

    db_path = get_db_path()

    if read_only and os.path.exists(db_path):
        _connection = duckdb.connect(db_path, read_only=True)
    else:
        _connection = duckdb.connect(db_path)

    # Disable progress bar for programmatic use
    try:
        _connection.execute("SET enable_progress_bar = false")
    except Exception:
        pass  # Older DuckDB versions may not support this

    return _connection


def ensure_database() -> tuple[str, bool]:
    """Ensure the database exists and is seeded. Returns (path, is_new)."""
    db_path = get_db_path()
    is_new = not os.path.exists(db_path)

    if is_new:
        from db.seed import seed_database
        seed_database(db_path)

    return db_path, is_new


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass
