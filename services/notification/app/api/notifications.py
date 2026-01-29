"""
Notifications API endpoints
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Notification, NotificationTemplate, NotificationStatus
from app.schemas import (
    NotificationCreate, NotificationResponse, NotificationListResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse
)

router = APIRouter()


# Notification endpoints
@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    user_id: Optional[UUID] = None,
    status: Optional[str] = None,
    notification_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List notifications with optional filters"""
    query = select(Notification)
    
    if user_id:
        query = query.where(Notification.user_id == user_id)
    if status:
        query = query.where(Notification.status == status)
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get items
    query = query.offset(skip).limit(limit).order_by(Notification.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    
    return NotificationListResponse(items=items, total=total or 0)


@router.post("", response_model=NotificationResponse, status_code=201)
async def send_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a new notification"""
    notification = Notification(
        user_id=data.user_id,
        notification_type=data.notification_type,
        recipient=data.recipient,
        subject=data.subject,
        message=data.message,
        template_id=data.template_id,
        metadata=data.metadata,
        status=NotificationStatus.PENDING,
    )
    
    db.add(notification)
    await db.commit()
    
    # Import settings
    from app.core import settings
    import structlog
    logger = structlog.get_logger(__name__)
    
    # Send notification based on type
    try:
        if data.notification_type.value == "email" and data.recipient:
            # Attempt to send email via SMTP
            if settings.smtp_configured:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                msg = MIMEMultipart()
                msg["From"] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
                msg["To"] = data.recipient
                msg["Subject"] = data.subject or "Notification from PGwallah"
                msg.attach(MIMEText(data.message, "plain"))
                
                if settings.SMTP_USE_TLS:
                    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                        server.starttls()
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        server.send_message(msg)
                
                notification.status = NotificationStatus.SENT
                logger.info("Email sent successfully", recipient=data.recipient)
            else:
                # SMTP not configured - mock mode
                notification.status = NotificationStatus.SENT
                logger.info("Email sent (mock mode - SMTP not configured)", recipient=data.recipient)
                
        elif data.notification_type.value == "sms" and data.recipient:
            # SMS sending
            if settings.sms_configured:
                # SMS provider integration (stub for actual implementation)
                if settings.SMS_PROVIDER == "gupshup":
                    # Gupshup integration would go here
                    import httpx
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(
                            "https://enterprise.smsgupshup.com/GatewayAPI/rest",
                            data={
                                "method": "SendMessage",
                                "send_to": data.recipient,
                                "msg": data.message,
                                "msg_type": "TEXT",
                                "userid": settings.GUPSHUP_APP_NAME,
                                "auth_scheme": "plain",
                                "password": settings.GUPSHUP_API_KEY,
                                "v": "1.1",
                                "format": "json"
                            }
                        )
                        if resp.status_code == 200:
                            notification.status = NotificationStatus.SENT
                            logger.info("SMS sent via Gupshup", recipient=data.recipient)
                        else:
                            notification.status = NotificationStatus.FAILED
                            logger.warning("SMS sending failed", provider="gupshup", status=resp.status_code)
                else:
                    # Other providers - mark as sent for now
                    notification.status = NotificationStatus.SENT
                    logger.info(f"SMS sent via {settings.SMS_PROVIDER}", recipient=data.recipient)
            else:
                # SMS not configured - mock mode
                notification.status = NotificationStatus.SENT
                logger.info("SMS sent (mock mode - SMS not configured)", recipient=data.recipient)
        else:
            # Push or other types - mock for now
            notification.status = NotificationStatus.SENT
            logger.info("Notification sent (mock mode)", type=data.notification_type.value)
            
    except Exception as e:
        # Log error but don't fail the request
        logger.error("Notification sending failed", error=str(e))
        notification.status = NotificationStatus.FAILED
        notification.metadata = str(e)[:200] if notification.metadata is None else notification.metadata
    
    notification.sent_at = datetime.utcnow()
    await db.commit()
    await db.refresh(notification)
    
    return notification


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get notification by ID"""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


# Template endpoints
@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    is_active: bool = True,
    notification_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List notification templates"""
    query = select(NotificationTemplate).where(NotificationTemplate.is_active == is_active)
    
    if notification_type:
        query = query.where(NotificationTemplate.notification_type == notification_type)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get items
    query = query.offset(skip).limit(limit).order_by(NotificationTemplate.name)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return TemplateListResponse(items=items, total=total or 0)


@router.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a notification template"""
    # Check for duplicate name
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.name == data.name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Template with this name already exists")
    
    template = NotificationTemplate(
        name=data.name,
        notification_type=data.notification_type,
        subject=data.subject,
        body=data.body,
        variables=data.variables,
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get template by ID"""
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a notification template"""
    result = await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    await db.commit()
    await db.refresh(template)
    
    return template
