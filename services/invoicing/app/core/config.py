from decimal import Decimal
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # App
    APP_NAME: str = "PGwallah Invoicing Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8040
    RELOAD: bool = True

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://invoicing_user:invoicing_password@postgres-invoicing:5432/invoicing_db")
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Inter-service URLs
    BOOKING_SERVICE_URL: str = Field(default="http://booking:8020/api")
    MESS_SERVICE_URL: str = Field(default="http://mess:8050/api")
    PAYMENT_SERVICE_URL: str = Field(default="http://payment:8030/api")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://notification:8070/api")

    # MinIO / S3 for PDF storage
    MINIO_ENDPOINT: str = Field(default="minio:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin123")
    MINIO_BUCKET: str = Field(default="invoices")
    MINIO_USE_SSL: bool = Field(default=False)

    # GST Settings
    DEFAULT_GST_RATE: float = Field(default=18.0)
    COMPANY_GSTIN: str = Field(default="")
    PLACE_OF_SUPPLY: str = Field(default="Karnataka")

    # Mess Settings
    MEAL_RATE: Decimal = Field(default=Decimal("50.00"))

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()