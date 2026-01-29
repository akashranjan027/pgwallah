"""
Database models for Notification Service
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class NotificationType(str, PyEnum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, PyEnum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(Base):
    """Notification record"""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.EMAIL)
    recipient = Column(String(255), nullable=False)  # Email or phone
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    template_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(Text, nullable=True)  # JSON additional data


class NotificationTemplate(Base):
    """Notification template"""
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    notification_type = Column(Enum(NotificationType), default=NotificationType.EMAIL)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    variables = Column(Text, nullable=True)  # JSON list of variable names
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
