"""
Settings for Orders service
"""
from functools import lru_cache
from typing import Optional, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "PGwallah Orders Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8060
    RELOAD: bool = True

    # Database (default to local SQLite for dev)
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./orders.db")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # External services
    MESS_SERVICE_URL: Optional[str] = Field(default=None)  # e.g. http://mess:8050

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def database_url_str(self) -> str:
        """
        Normalize DB URL to async driver for Postgres if needed.
        - postgresql://... -> postgresql+asyncpg://...
        - sqlite+aiosqlite stays as is
        """
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()


settings = get_settings()