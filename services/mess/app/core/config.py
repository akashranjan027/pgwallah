"""
Configuration settings for Mess service
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

    # Application
    APP_NAME: str = "PGwallah Mess Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8050)
    RELOAD: bool = Field(default=True)

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://mess_user:mess_password@postgres-mess:5432/mess_db")
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Coupons
    DAILY_MEAL_SLOTS: List[str] = Field(default=["breakfast", "lunch", "snacks", "dinner"])

    # Logging
    LOG_LEVEL: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()


settings = get_settings()