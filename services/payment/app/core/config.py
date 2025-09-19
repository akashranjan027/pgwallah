"""
Configuration settings for Payment service
"""
from functools import lru_cache
from typing import Optional

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
    APP_NAME: str = "PGwallah Payment Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = Field(default=True)
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8030)
    RELOAD: bool = Field(default=True)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://payment_user:payment_password@localhost:5434/payment_db"
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)

    # Redis
    REDIS_URL: str = Field(
        default="redis://:redis_password@localhost:6379/2"
    )

    # RabbitMQ
    RABBITMQ_URL: str = Field(
        default="amqp://rabbitmq_user:rabbitmq_password@localhost:5672/"
    )
    
    # Razorpay Settings
    RAZORPAY_KEY_ID: str = Field(default="rzp_test_dummy_key")
    RAZORPAY_KEY_SECRET: str = Field(default="dummy_secret")
    RAZORPAY_WEBHOOK_SECRET: str = Field(default="webhook_secret")
    
    # UPI Settings
    UPI_VPA: str = Field(default="pgwallah@razorpay")
    
    # MinIO/S3 Settings
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin123")
    MINIO_BUCKET_RECEIPTS: str = Field(default="receipts")
    MINIO_SECURE: bool = Field(default=False)

    # External Services
    AUTH_SERVICE_URL: str = Field(default="http://localhost:8010")
    BOOKING_SERVICE_URL: str = Field(default="http://localhost:8020")
    INVOICING_SERVICE_URL: str = Field(default="http://localhost:8040")

    # Payment Settings
    DEFAULT_CURRENCY: str = Field(default="INR")
    MIN_PAYMENT_AMOUNT: float = Field(default=1.0)  # ₹1
    MAX_PAYMENT_AMOUNT: float = Field(default=100000.0)  # ₹1 Lakh
    PAYMENT_TIMEOUT_MINUTES: int = Field(default=15)
    
    # Subscription Settings
    RENT_PLAN_INTERVAL: str = Field(default="monthly")
    RENT_PLAN_INTERVAL_COUNT: int = Field(default=1)
    
    # Webhook Settings
    WEBHOOK_TIMEOUT_SECONDS: int = Field(default=30)
    WEBHOOK_RETRY_ATTEMPTS: int = Field(default=3)
    
    # Security
    ALLOWED_IPS_RAZORPAY: list[str] = Field(
        default=[
            "3.6.119.166",
            "3.7.75.26", 
            "13.232.74.182",
            "52.66.237.167"
        ]
    )  # Razorpay webhook IPs
    
    # CORS
    ALLOWED_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def razorpay_config(self) -> dict[str, str]:
        return {
            "key_id": self.RAZORPAY_KEY_ID,
            "key_secret": self.RAZORPAY_KEY_SECRET,
        }

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() in ("test", "testing")

    @property
    def database_url_str(self) -> str:
        # Keep a dedicated property to match existing references in database.py
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()