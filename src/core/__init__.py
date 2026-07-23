"""Core modules for the Science of Reading MCP server.

Contains meta-tool router and structured error handling.
"""

from src.core.errors import (
    SoRErrorCode,
    ERROR_MESSAGES,
    format_error,
)
from src.core.router import query_sor_curriculum

__all__ = [
    "SoRErrorCode",
    "ERROR_MESSAGES",
    "format_error",
    "query_sor_curriculum",
]
