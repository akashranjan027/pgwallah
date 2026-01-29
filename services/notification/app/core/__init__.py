"""
Configuration settings for Notification Service
"""
import os
from typing import List, Optional
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Notification service settings with production-ready configuration"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application settings
    APP_NAME: str = "PGwallah Notification Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8070)
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://notification_user:notification_password@postgres-notification:5432/notification_db"
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    
    # Email settings (SMTP)
    SMTP_HOST: str = Field(default="smtp.example.com", description="SMTP server hostname")
    SMTP_PORT: int = Field(default=587, description="SMTP server port (587 for TLS, 465 for SSL)")
    SMTP_USER: str = Field(default="", description="SMTP authentication username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP authentication password")
    SMTP_USE_TLS: bool = Field(default=True, description="Use TLS encryption")
    FROM_EMAIL: str = Field(default="noreply@pgwallah.com", description="Sender email address")
    FROM_NAME: str = Field(default="PGwallah", description="Sender name")
    
    # SMS Provider Settings (MSG91/Gupshup/Twilio)
    SMS_PROVIDER: str = Field(default="gupshup", description="SMS provider: gupshup, msg91, twilio")
    
    # Gupshup
    GUPSHUP_API_KEY: str = Field(default="", description="Gupshup API key")
    GUPSHUP_APP_NAME: str = Field(default="PGwallah", description="Gupshup app name")
    
    # MSG91
    MSG91_AUTH_KEY: str = Field(default="", description="MSG91 auth key")
    MSG91_SENDER_ID: str = Field(default="PGWALL", description="6-char sender ID for MSG91")
    MSG91_TEMPLATE_ID: str = Field(default="", description="MSG91 DLT template ID")
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = Field(default="", description="Twilio account SID")
    TWILIO_AUTH_TOKEN: str = Field(default="", description="Twilio auth token")
    TWILIO_PHONE_NUMBER: str = Field(default="", description="Twilio phone number for sending SMS")
    
    # Push Notifications (Firebase)
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(default=None, description="Path to Firebase service account JSON")
    
    # RabbitMQ for async processing
    RABBITMQ_URL: str = Field(default="amqp://rabbitmq_user:rabbitmq_password@rabbitmq:5672/")
    
    # Redis for rate limiting
    REDIS_URL: str = Field(default="redis://:redis_password@redis:6379/6")
    
    # Rate limiting
    EMAIL_RATE_LIMIT_PER_HOUR: int = Field(default=100, description="Max emails per hour per user")
    SMS_RATE_LIMIT_PER_HOUR: int = Field(default=10, description="Max SMS per hour per user")
    
    # CORS settings
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
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured for sending emails."""
        return bool(self.SMTP_HOST and self.SMTP_HOST != "smtp.example.com" and self.SMTP_USER)
    
    @property
    def sms_configured(self) -> bool:
        """Check if SMS provider is properly configured."""
        if self.SMS_PROVIDER == "gupshup":
            return bool(self.GUPSHUP_API_KEY)
        elif self.SMS_PROVIDER == "msg91":
            return bool(self.MSG91_AUTH_KEY)
        elif self.SMS_PROVIDER == "twilio":
            return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN)
        return False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
