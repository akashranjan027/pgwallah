"""
Configuration settings for Auth service
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn
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
    APP_NAME: str = "PGwallah Auth Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = Field(default=True)
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8010)
    RELOAD: bool = Field(default=True)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_db"
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)

    # Redis
    REDIS_URL: RedisDsn = Field(
        default="redis://:redis_password@localhost:6379/0"
    )
    REDIS_TIMEOUT: int = Field(default=30)

    # JWT Settings
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="RS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)  # 30 days
    JWT_ISSUER: str = Field(default="pgwallah-auth")
    JWT_AUDIENCE: str = Field(default="pgwallah")

    # Password hashing
    PWD_CONTEXT_SCHEMES: list[str] = Field(default=["bcrypt"])
    PWD_CONTEXT_DEPRECATED: str = Field(default="auto")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000)

    # CORS
    ALLOWED_HOSTS: list[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"]
    )
    ALLOWED_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Monitoring
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field(default="json")

    # External Services (for future use)
    EMAIL_SERVICE_URL: Optional[str] = Field(default=None)
    SMS_SERVICE_URL: Optional[str] = Field(default=None)

    # Security
    ALLOWED_IPS: list[str] = Field(default=["0.0.0.0/0"])  # Allow all in development
    MAX_LOGIN_ATTEMPTS: int = Field(default=5)
    LOGIN_ATTEMPT_TIMEOUT_MINUTES: int = Field(default=15)
    
    # Development/Testing
    TESTING: bool = Field(default=False)
    TEST_DATABASE_URL: Optional[PostgresDsn] = Field(default=None)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.TESTING

    @property
    def database_url_str(self) -> str:
        """Get database URL as string"""
        return self.DATABASE_URL if not self.is_testing else str(self.TEST_DATABASE_URL or self.DATABASE_URL)

    @property
    def redis_url_str(self) -> str:
        """Get Redis URL as string"""
        return str(self.REDIS_URL)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()