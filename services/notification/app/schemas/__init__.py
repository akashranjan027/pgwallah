"""
Pydantic schemas for Notification Service
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# Enums
class NotificationType(str):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


# Notification Schemas
class NotificationCreate(BaseModel):
    user_id: UUID
    notification_type: str = "email"
    recipient: str = Field(..., min_length=1)
    subject: Optional[str] = None
    message: str = Field(..., min_length=1)
    template_id: Optional[UUID] = None
    metadata: Optional[str] = None


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    notification_type: str
    recipient: str
    subject: Optional[str] = None
    message: str
    template_id: Optional[UUID] = None
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int


# Template Schemas
class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    notification_type: str = "email"
    subject: Optional[str] = None
    body: str = Field(..., min_length=1)
    variables: Optional[str] = None


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    notification_type: str
    subject: Optional[str] = None
    body: str
    variables: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    items: List[TemplateResponse]
    total: int
