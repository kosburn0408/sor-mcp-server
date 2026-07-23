"""Configuration via Pydantic BaseSettings with environment variable support.

All settings are prefixed with SOR_. Override via env vars or .env file.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Science of Reading MCP server configuration.

    Loaded from environment variables prefixed with SOR_ (e.g., SOR_API_BASE_URL).
    """

    sor_api_base_url: str = "https://sor.edtechlabs.dev/api/v1"
    sor_api_key: str = ""
    request_timeout: float = 10.0
    cache_ttl_seconds: int = 300  # 5 minutes for static data
    max_retries: int = 3
    retry_backoff_base: float = 1.0  # seconds

    model_config = SettingsConfigDict(
        env_prefix="SOR_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
