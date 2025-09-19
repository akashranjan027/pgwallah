"""
Payment API endpoints with Razorpay UPI integration
"""
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional, List

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.integrations.razorpay_client import razorpay_client
from app.models.payment import Ledger, Payment, PaymentIntent, PaymentStatus, Subscription, RentPayment, PG, PGAdmin, PGMembership, AdvancePayment
from app.schemas.payment import (
    CreatePaymentIntentRequest,
    CreateSubscriptionRequest,
    PaymentIntentResponse,
    PaymentResponse,
    SubscriptionResponse,
    WebhookResponse,
    CreateDummyRentPaymentRequest,
    RentPaymentResponse,
)
from app.utils.events import publish_payment_event
from app.utils.receipts import generate_receipt

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/intents", response_model=PaymentIntentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create payment intent for rent, deposit, or other charges"""
    
    logger.info(
        "Creating payment intent",
        tenant_id=str(request.tenant_id),
        amount=request.amount,
        purpose=request.purpose,
    )

    # Create internal payment intent
    payment_intent = PaymentIntent(
        tenant_id=request.tenant_id,
        amount=request.amount,
        currency=request.currency,
        purpose=request.purpose,
        description=request.description,
        booking_id=request.booking_id,
        due_date=request.due_date,
        metadata=json.dumps(request.metadata) if request.metadata else None,
    )
    
    db.add(payment_intent)
    await db.flush()

    try:
        # Create Razorpay order
        receipt = f"PG_{request.purpose}_{payment_intent.id}"
        notes = {
            "tenant_id": str(request.tenant_id),
            "purpose": request.purpose,
            "payment_intent_id": str(payment_intent.id),
        }
        
        if request.booking_id:
            notes["booking_id"] = str(request.booking_id)

        razorpay_order = await razorpay_client.create_order(
            amount=request.amount,
            receipt=receipt,
            notes=notes,
            currency=request.currency,
        )

        # Update payment intent with Razorpay order ID
        payment_intent.razorpay_order_id = razorpay_order["id"]
        payment_intent.status = PaymentStatus.PENDING

        await db.commit()

        # Generate UPI intent URL for mobile apps
        upi_intent_url = await razorpay_client.get_upi_intent_url(
            razorpay_order["id"], request.amount
        )

        logger.info(
            "Payment intent created successfully",
            payment_intent_id=str(payment_intent.id),
            razorpay_order_id=razorpay_order["id"],
        )

        return PaymentIntentResponse(
            id=payment_intent.id,
            razorpay_order_id=razorpay_order["id"],
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            purpose=payment_intent.purpose,
            status=payment_intent.status,
            upi_intent_url=upi_intent_url,
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
            created_at=payment_intent.created_at,
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to create payment intent",
            payment_intent_id=str(payment_intent.id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )


@router.get("/intents/{intent_id}", response_model=PaymentIntentResponse)
async def get_payment_intent(
    intent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get payment intent details"""
    
    stmt = select(PaymentIntent).where(PaymentIntent.id == intent_id)
    result = await db.execute(stmt)
    payment_intent = result.scalar_one_or_none()
    
    if not payment_intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found"
        )

    upi_intent_url = None
    if payment_intent.razorpay_order_id and payment_intent.status == PaymentStatus.PENDING:
        upi_intent_url = await razorpay_client.get_upi_intent_url(
            payment_intent.razorpay_order_id, payment_intent.amount
        )

    return PaymentIntentResponse(
        id=payment_intent.id,
        razorpay_order_id=payment_intent.razorpay_order_id,
        amount=payment_intent.amount,
        currency=payment_intent.currency,
        purpose=payment_intent.purpose,
        status=payment_intent.status,
        upi_intent_url=upi_intent_url,
        razorpay_key_id=settings.RAZORPAY_KEY_ID,
        created_at=payment_intent.created_at,
    )


@router.post("/webhooks/razorpay", response_model=WebhookResponse)
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Handle Razorpay webhooks for payment status updates"""
    
    # Get webhook payload and signature
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    logger.info(
        "Received Razorpay webhook",
        signature_present=bool(signature),
        payload_size=len(payload),
    )

    # Verify webhook signature in production
    if settings.is_production:
        if not razorpay_client.verify_webhook_signature(
            payload.decode(), signature
        ):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

    try:
        webhook_data = json.loads(payload.decode())
        event = webhook_data.get("event")
        payment_data = webhook_data.get("payload", {}).get("payment", {}).get("entity", {})
        
        logger.info(
            "Processing webhook event",
            event=event,
            payment_id=payment_data.get("id"),
            order_id=payment_data.get("order_id"),
            status=payment_data.get("status"),
        )

        if event in ["payment.authorized", "payment.captured", "payment.failed"]:
            await process_payment_webhook(payment_data, webhook_data, background_tasks, db)
        elif event in ["subscription.activated", "subscription.charged", "subscription.cancelled"]:
            await process_subscription_webhook(webhook_data, background_tasks, db)

        return WebhookResponse(status="success", message="Webhook processed successfully")

    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


async def process_payment_webhook(
    payment_data: Dict,
    webhook_data: Dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
):
    """Process payment-related webhook events"""
    
    razorpay_payment_id = payment_data.get("id")
    razorpay_order_id = payment_data.get("order_id")
    payment_status = payment_data.get("status")

    if not razorpay_order_id:
        logger.warning("No order ID in webhook payload")
        return

    # Find payment intent
    stmt = select(PaymentIntent).where(PaymentIntent.razorpay_order_id == razorpay_order_id)
    result = await db.execute(stmt)
    payment_intent = result.scalar_one_or_none()

    if not payment_intent:
        logger.warning("Payment intent not found", order_id=razorpay_order_id)
        return

    # Map Razorpay status to our status
    status_mapping = {
        "authorized": PaymentStatus.AUTHORIZED,
        "captured": PaymentStatus.CAPTURED,
        "failed": PaymentStatus.FAILED,
    }
    
    new_status = status_mapping.get(payment_status, PaymentStatus.PENDING)

    # Create or update payment record
    if payment_status in ["authorized", "captured"]:
        # Create payment record
        payment = Payment(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            payment_intent_id=payment_intent.id,
            tenant_id=payment_intent.tenant_id,
            amount=Decimal(payment_data.get("amount", 0)) / 100,  # Convert paise to rupees
            currency=payment_data.get("currency", "INR"),
            status=new_status,
            method=payment_data.get("method"),
            fee=Decimal(payment_data.get("fee", 0)) / 100 if payment_data.get("fee") else None,
            tax=Decimal(payment_data.get("tax", 0)) / 100 if payment_data.get("tax") else None,
            razorpay_webhook_payload=json.dumps(webhook_data),
            processed_at=datetime.utcnow(),
        )
        
        db.add(payment)

        # Create ledger entries for double-entry bookkeeping
        await create_ledger_entries(payment, payment_intent, db)

        # Generate receipt
        background_tasks.add_task(generate_receipt, payment.id)

    # Update payment intent status
    payment_intent.status = new_status
    await db.commit()

    # Publish payment event
    event_data = {
        "payment_intent_id": str(payment_intent.id),
        "tenant_id": str(payment_intent.tenant_id),
        "amount": float(payment_intent.amount),
        "purpose": payment_intent.purpose,
        "status": new_status.value,
        "razorpay_payment_id": razorpay_payment_id,
    }

    background_tasks.add_task(
        publish_payment_event,
        "payment.succeeded" if new_status == PaymentStatus.CAPTURED else "payment.failed",
        event_data,
    )

    logger.info(
        "Payment webhook processed",
        payment_intent_id=str(payment_intent.id),
        status=new_status.value,
    )


async def process_subscription_webhook(
    webhook_data: Dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
):
    """Process subscription-related webhook events"""
    
    subscription_data = webhook_data.get("payload", {}).get("subscription", {}).get("entity", {})
    event = webhook_data.get("event")
    
    razorpay_subscription_id = subscription_data.get("id")
    
    if not razorpay_subscription_id:
        logger.warning("No subscription ID in webhook payload")
        return

    # Find subscription
    stmt = select(Subscription).where(
        Subscription.razorpay_subscription_id == razorpay_subscription_id
    )
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning("Subscription not found", subscription_id=razorpay_subscription_id)
        return

    # Update subscription based on event
    if event == "subscription.activated":
        subscription.status = "active"
    elif event == "subscription.charged":
        subscription.paid_count += 1
        if subscription.total_count:
            subscription.remaining_count = subscription.total_count - subscription.paid_count
    elif event == "subscription.cancelled":
        subscription.status = "cancelled"

    await db.commit()

    logger.info(
        "Subscription webhook processed",
        subscription_id=razorpay_subscription_id,
        event=event,
        status=subscription.status,
    )


async def create_ledger_entries(
    payment: Payment,
    payment_intent: PaymentIntent,
    db: AsyncSession,
):
    """Create double-entry ledger entries for payment"""
    
    transaction_id = f"PAY_{payment.razorpay_payment_id}"
    
    # Debit: Cash/Bank (Asset increases)
    cash_entry = Ledger(
        tenant_id=payment.tenant_id,
        transaction_id=transaction_id,
        account="cash_and_bank",
        debit=payment.amount,
        description=f"Payment received for {payment_intent.purpose}",
        reference_type="payment",
        reference_id=payment.id,
    )
    
    # Credit: Revenue account (Revenue increases)
    revenue_account = {
        "rent": "rent_revenue",
        "deposit": "security_deposits",
        "mess": "mess_revenue",
    }.get(payment_intent.purpose, "other_revenue")
    
    revenue_entry = Ledger(
        tenant_id=payment.tenant_id,
        transaction_id=transaction_id,
        account=revenue_account,
        credit=payment.amount,
        description=f"Revenue from {payment_intent.purpose}",
        reference_type="payment",
        reference_id=payment.id,
    )
    
    db.add_all([cash_entry, revenue_entry])

    logger.info(
        "Created ledger entries",
        payment_id=str(payment.id),
        amount=payment.amount,
        accounts=[cash_entry.account, revenue_entry.account],
    )


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    request: CreateSubscriptionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create recurring subscription for monthly rent"""
    
    logger.info(
        "Creating subscription",
        tenant_id=str(request.tenant_id),
        plan_id=request.plan_id,
        booking_id=str(request.booking_id),
    )

    try:
        # Create Razorpay subscription
        razorpay_subscription = await razorpay_client.create_subscription(
            plan_id=request.plan_id,
            customer_notify=request.customer_notify,
            total_count=request.total_count,
            notes={
                "tenant_id": str(request.tenant_id),
                "booking_id": str(request.booking_id),
            },
        )

        # Create internal subscription record
        subscription = Subscription(
            razorpay_subscription_id=razorpay_subscription["id"],
            razorpay_plan_id=request.plan_id,
            tenant_id=request.tenant_id,
            booking_id=request.booking_id,
            amount=Decimal(razorpay_subscription["plan"]["item"]["amount"]) / 100,
            currency=razorpay_subscription["plan"]["item"]["currency"],
            start_date=datetime.utcfromtimestamp(razorpay_subscription["start_at"]),
            total_count=request.total_count,
            remaining_count=request.total_count,
        )

        db.add(subscription)
        await db.commit()

        logger.info(
            "Subscription created successfully",
            subscription_id=str(subscription.id),
            razorpay_subscription_id=razorpay_subscription["id"],
        )

        return SubscriptionResponse(
            id=subscription.id,
            razorpay_subscription_id=subscription.razorpay_subscription_id,
            tenant_id=subscription.tenant_id,
            booking_id=subscription.booking_id,
            amount=subscription.amount,
            status=subscription.status,
            start_date=subscription.start_date,
            created_at=subscription.created_at,
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            "Failed to create subscription",
            tenant_id=str(request.tenant_id),
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.get("/receipts")
async def get_receipts(
    tenant_id: Optional[uuid.UUID] = None,
    payment_intent_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get payment receipts for tenant"""
    
    stmt = select(Payment)
    
    if tenant_id:
        stmt = stmt.where(Payment.tenant_id == tenant_id)
    
    if payment_intent_id:
        stmt = stmt.where(Payment.payment_intent_id == payment_intent_id)
    
    stmt = stmt.where(Payment.status == PaymentStatus.CAPTURED)
    stmt = stmt.order_by(Payment.created_at.desc())
    
    result = await db.execute(stmt)
    payments = result.scalars().all()

    receipts = []
    for payment in payments:
        receipts.append({
            "id": payment.id,
            "razorpay_payment_id": payment.razorpay_payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "method": payment.method,
            "receipt_url": payment.receipt_url,
            "processed_at": payment.processed_at,
            "created_at": payment.created_at,
        })

    return {"receipts": receipts}


@router.post("/verify")
async def verify_payment(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Verify payment signature from frontend"""
    
    data = await request.json()
    
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required payment verification data"
        )

    # Verify payment signature
    is_valid = razorpay_client.verify_payment_signature(
        razorpay_order_id, razorpay_payment_id, razorpay_signature
    )

    if not is_valid:
        logger.warning(
            "Invalid payment signature",
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )

    # Find and update payment intent
    stmt = select(PaymentIntent).where(PaymentIntent.razorpay_order_id == razorpay_order_id)
    result = await db.execute(stmt)
    payment_intent = result.scalar_one_or_none()

    if not payment_intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment intent not found"
        )

    # Fetch payment details from Razorpay
    try:
        payment_details = await razorpay_client.fetch_payment(razorpay_payment_id)
        
        # Create payment record
        payment = Payment(
            razorpay_payment_id=razorpay_payment_id,
            razorpay_order_id=razorpay_order_id,
            razorpay_signature=razorpay_signature,
            payment_intent_id=payment_intent.id,
            tenant_id=payment_intent.tenant_id,
            amount=Decimal(payment_details["amount"]) / 100,
            currency=payment_details["currency"],
            status=PaymentStatus.CAPTURED,
            method=payment_details.get("method"),
            fee=Decimal(payment_details.get("fee", 0)) / 100,
            tax=Decimal(payment_details.get("tax", 0)) / 100,
            processed_at=datetime.utcnow(),
        )
        
        db.add(payment)

        # Update payment intent
        payment_intent.status = PaymentStatus.CAPTURED

        # Create ledger entries
        await create_ledger_entries(payment, payment_intent, db)

        await db.commit()

        # Generate receipt and publish event
        background_tasks.add_task(generate_receipt, payment.id)
        background_tasks.add_task(
            publish_payment_event,
            "payment.succeeded",
            {
                "payment_intent_id": str(payment_intent.id),
                "payment_id": str(payment.id),
                "tenant_id": str(payment_intent.tenant_id),
                "amount": float(payment.amount),
                "purpose": payment_intent.purpose,
            },
        )

        logger.info(
            "Payment verified and recorded",
            payment_id=str(payment.id),
            amount=payment.amount,
        )

        return {"status": "success", "payment_id": payment.id}

    except Exception as e:
        await db.rollback()
        logger.error("Payment verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment verification failed"
        )


async def process_subscription_webhook(
    webhook_data: Dict,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
):
    """Process subscription webhook events"""
    # Implementation for subscription webhooks
    logger.info("Processing subscription webhook", event=webhook_data.get("event"))
    pass


# =========================
# Dummy rent payment flows
# =========================

@router.post("/dummy/rent", response_model=RentPaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_dummy_rent_payment(
    request: CreateDummyRentPaymentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a dummy rent payment without external gateway.
    - Creates a PaymentIntent with purpose 'rent'
    - Immediately marks as CAPTURED and records a RentPayment row
    - No UPI/Card integration used (placeholder for future)
    """
    logger.info(
        "Creating dummy rent payment",
        tenant_id=str(request.tenant_id),
        room_no=request.room_no,
        amount=float(request.amount),
    )

    # 1) Create internal payment intent (no gateway order id)
    intent = PaymentIntent(
        tenant_id=request.tenant_id,
        amount=request.amount,
        currency="INR",
        purpose="rent",
        description=f"Dummy rent payment for room {request.room_no}",
        metadata=json.dumps({"room_no": request.room_no, "dummy": True}),
        due_date=request.due_date,
        status=PaymentStatus.CAPTURED,
    )
    db.add(intent)
    await db.flush()

    # 2) Create RentPayment record (dummy CAPTURED)
    rent_payment = RentPayment(
        payment_intent_id=intent.id,
        tenant_id=request.tenant_id,
        room_no=request.room_no,
        amount=request.amount,
        status=PaymentStatus.CAPTURED,
        due_date=request.due_date,
        payment_date=request.payment_date or datetime.utcnow(),
    )
    db.add(rent_payment)

    # Note: Optionally create ledger entries for dummy flows (future)
    # TODO: create ledger entries for rent (rent_receivable -> rent_revenue)

    await db.commit()
    await db.refresh(rent_payment)

    # TODO: generate invoice via invoicing service
    # Emit event for invoicing/notifications
    background_tasks.add_task(
        publish_payment_event,
        "rent.payment.recorded",
        {
            "payment_intent_id": str(intent.id),
            "tenant_id": str(request.tenant_id),
            "room_no": request.room_no,
            "amount": float(request.amount),
            "due_date": request.due_date.isoformat() if request.due_date else None,
            "payment_date": (request.payment_date or datetime.utcnow()).isoformat(),
        },
    )

    return RentPaymentResponse(
        id=rent_payment.id,
        payment_intent_id=rent_payment.payment_intent_id,
        tenant_id=rent_payment.tenant_id,
        room_no=rent_payment.room_no,
        amount=rent_payment.amount,
        status=rent_payment.status,
        due_date=rent_payment.due_date,
        payment_date=rent_payment.payment_date,
        created_at=rent_payment.created_at,
    )


@router.get("/admin/rent", response_model=List[RentPaymentResponse])
async def admin_list_rent_payments(
    tenant_id: Optional[uuid.UUID] = None,
    room_no: Optional[str] = None,
    status_filter: Optional[PaymentStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin listing of rent payments with filters.
    TODO: Protect with admin auth once gateway + RBAC are wired.
    """
    stmt = select(RentPayment)
    if tenant_id:
        stmt = stmt.where(RentPayment.tenant_id == tenant_id)
    if room_no:
        # simple ilike; for SQLite fallback, keep equality
        try:
            from sqlalchemy import or_
            stmt = stmt.where(RentPayment.room_no.ilike(f"%{room_no}%"))
        except Exception:
            stmt = stmt.where(RentPayment.room_no == room_no)
    if status_filter:
        stmt = stmt.where(RentPayment.status == status_filter)
    if start_date:
        stmt = stmt.where(RentPayment.payment_date >= start_date)
    if end_date:
        stmt = stmt.where(RentPayment.payment_date <= end_date)

    stmt = stmt.order_by(RentPayment.created_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        RentPaymentResponse(
            id=r.id,
            payment_intent_id=r.payment_intent_id,
            tenant_id=r.tenant_id,
            room_no=r.room_no,
            amount=r.amount,
            status=r.status,
            due_date=r.due_date,
            payment_date=r.payment_date,
            created_at=r.created_at,
        )
        for r in rows
    ]


# =========================
# PG / Admin / Membership
# =========================

class CreatePGRequest(BaseModel):
    name: str = Field(..., max_length=200)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=20)


class PGResponse(BaseModel):
    id: UUID
    name: str
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AddPGAdminRequest(BaseModel):
    pg_id: UUID
    user_id: UUID
    role: str = Field(default="admin", max_length=50)


class PGAdminResponse(BaseModel):
    id: UUID
    pg_id: UUID
    user_id: UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class AddMembershipRequest(BaseModel):
    pg_id: UUID
    tenant_id: UUID
    room_no: str = Field(..., max_length=50)
    rent_amount: Decimal
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PGMembershipResponse(BaseModel):
    id: UUID
    pg_id: UUID
    tenant_id: UUID
    room_no: str
    rent_amount: Decimal
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/admin/pg", response_model=PGResponse, status_code=status.HTTP_201_CREATED)
async def create_pg(request: CreatePGRequest, db: AsyncSession = Depends(get_db)):
    pg = PG(
        name=request.name,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        pincode=request.pincode,
    )
    db.add(pg)
    await db.commit()
    await db.refresh(pg)
    return PGResponse.model_validate(pg)


@router.get("/admin/pg", response_model=List[PGResponse])
async def list_pgs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PG).order_by(PG.created_at.desc()))
    rows = result.scalars().all()
    return [PGResponse.model_validate(r) for r in rows]


@router.post("/admin/pg/admins", response_model=PGAdminResponse, status_code=status.HTTP_201_CREATED)
async def add_pg_admin(request: AddPGAdminRequest, db: AsyncSession = Depends(get_db)):
    # TODO: validate user_id exists in Auth service and has admin role
    admin = PGAdmin(pg_id=request.pg_id, user_id=request.user_id, role=request.role)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return PGAdminResponse.model_validate(admin)


@router.get("/admin/pg/{pg_id}/admins", response_model=List[PGAdminResponse])
async def list_pg_admins(pg_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PGAdmin).where(PGAdmin.pg_id == pg_id))
    rows = result.scalars().all()
    return [PGAdminResponse.model_validate(r) for r in rows]


@router.post("/admin/pg/memberships", response_model=PGMembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_membership(request: AddMembershipRequest, db: AsyncSession = Depends(get_db)):
    membership = PGMembership(
        pg_id=request.pg_id,
        tenant_id=request.tenant_id,
        room_no=request.room_no,
        rent_amount=request.rent_amount,
        start_date=request.start_date,
        end_date=request.end_date,
        active=True,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return PGMembershipResponse.model_validate(membership)


@router.get("/admin/pg/{pg_id}/memberships", response_model=List[PGMembershipResponse])
async def list_memberships(pg_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PGMembership).where(PGMembership.pg_id == pg_id).order_by(PGMembership.created_at.desc()))
    rows = result.scalars().all()
    return [PGMembershipResponse.model_validate(r) for r in rows]


@router.delete("/admin/pg/memberships/{membership_id}")
async def delete_membership(membership_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PGMembership).where(PGMembership.id == membership_id))
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    await db.delete(membership)
    await db.commit()
    return {"message": "Membership deleted"}


# =========================
# Dummy advance payments
# =========================

class CreateAdvancePaymentRequest(BaseModel):
    tenant_id: UUID
    pg_id: UUID
    amount: Decimal
    payment_date: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class AdvancePaymentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    pg_id: UUID
    amount: Decimal
    payment_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/dummy/advance", response_model=AdvancePaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_dummy_advance_payment(
    request: CreateAdvancePaymentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    adv = AdvancePayment(
        tenant_id=request.tenant_id,
        pg_id=request.pg_id,
        amount=request.amount,
        payment_date=request.payment_date or datetime.utcnow(),
        notes=request.notes,
    )
    db.add(adv)
    await db.commit()
    await db.refresh(adv)

    # TODO: generate invoice for advance or tie to deposit logic
    background_tasks.add_task(
        publish_payment_event,
        "advance.payment.recorded",
        {
            "tenant_id": str(request.tenant_id),
            "pg_id": str(request.pg_id),
            "amount": float(request.amount),
            "payment_date": (request.payment_date or datetime.utcnow()).isoformat(),
        },
    )

    return AdvancePaymentResponse.model_validate(adv)


@router.get("/admin/advance", response_model=List[AdvancePaymentResponse])
async def admin_list_advance_payments(
    tenant_id: Optional[UUID] = None,
    pg_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AdvancePayment)
    if tenant_id:
        stmt = stmt.where(AdvancePayment.tenant_id == tenant_id)
    if pg_id:
        stmt = stmt.where(AdvancePayment.pg_id == pg_id)
    if start_date:
        stmt = stmt.where(AdvancePayment.payment_date >= start_date)
    if end_date:
        stmt = stmt.where(AdvancePayment.payment_date <= end_date)
    stmt = stmt.order_by(AdvancePayment.created_at.desc())

    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [AdvancePaymentResponse.model_validate(r) for r in rows]