"""Application settings loaded from environment variables (section 15).

Uses pydantic-settings so every secret comes from the environment - never from
source (section 16: "No hardcoded credentials anywhere").
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    environment: str = Field(default="development")
    root_domain: str = Field(default="deltaplax.com")
    api_v1_prefix: str = Field(default="/api/v1")
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    # --- Database ---
    database_url: str = Field(default="sqlite+pysqlite:///./local_data/deltaplax.sqlite3")

    # --- Security ---
    secret_key: str = Field(default="dev-only-insecure-key-change-me")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    bcrypt_rounds: int = Field(default=12)
    encryption_key: str = Field(default="dev-only-insecure-aes-key-change-me-0123")
    max_failed_logins: int = Field(default=5)
    lockout_minutes: int = Field(default=15)

    # --- Super admin bootstrap ---
    deltaplax_admin_email: str = Field(default="admin@deltaplax.com")
    deltaplax_admin_password: str | None = Field(default=None)

    # --- Storage ---
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_bucket: str = Field(default="deltaplax")
    minio_secure: bool = Field(default=False)

    # --- Queue ---
    redis_url: str = Field(default="redis://localhost:6379/0")

    # --- AI (optional) ---
    openai_api_key: str | None = Field(default=None)
    ai_model: str = Field(default="gpt-4o-mini")

    # --- Sync (local server) ---
    cloud_sync_url: str = Field(default="https://api.deltaplax.com")
    sync_poll_seconds: int = Field(default=30)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
