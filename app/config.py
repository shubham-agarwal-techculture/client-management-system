"""Application configuration via pydantic-settings.

Values are loaded from `.env` / environment variables. All settings are
optional with sensible defaults so the system runs out of the box with SQLite.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Client Management System"
    app_env: str = Field("development", description="development | production | testing")
    debug: bool = True

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = Field(
        "sqlite+aiosqlite:///./cms.db",
        description="Async SQLAlchemy database URL (SQLite default)",
    )

    # --- Security ---
    secret_key: str = Field(
        "change-me-in-production",
        description="Secret used to sign JWT tokens",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12

    # --- Multi-tenancy ---
    multi_tenant: bool = Field(
        True,
        description="When true, every client/user must belong to an organization",
    )

    # --- Document storage ---
    storage_backend: str = Field(
        "local",
        description="local | s3 (pluggable via services.storage.StorageBackend)",
    )
    storage_local_path: str = Field(
        "./uploads",
        description="Local directory used when STORAGE_BACKEND=local",
    )
    storage_s3_bucket: Optional[str] = None
    storage_s3_region: Optional[str] = "us-east-1"
    storage_s3_endpoint_url: Optional[str] = None
    storage_s3_access_key: Optional[str] = None
    storage_s3_secret_key: Optional[str] = None

    # --- CORS ---
    cors_origins: str = Field(
        "http://localhost:8000,http://127.0.0.1:8000",
        description="Comma-separated list of allowed CORS origins",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- Seed data ---
    seed_demo_data: bool = True
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = "admin123"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()