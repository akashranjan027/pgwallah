"""
Pydantic schemas for payment endpoints
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.payment import PaymentStatus, PaymentMethod, SubscriptionStatus


class CreatePaymentIntentRequest(BaseModel):
    """Create payment intent request schema"""
    tenant_id: UUID = Field(..., description="Tenant ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount in rupees")
    currency: str = Field(default="INR", description="Currency code")
    purpose: str = Field(..., description="Payment purpose (rent, deposit, mess)")
    description: Optional[str] = Field(None, description="Payment description")
    booking_id: Optional[UUID] = Field(None, description="Associated booking ID")
    due_date: Optional[datetime] = Field(None, description="Payment due date")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")

    @validator('purpose')
    def validate_purpose(cls, v):
        allowed_purposes = ['rent', 'deposit', 'mess', 'maintenance', 'other']
        if v not in allowed_purposes:
            raise ValueError(f'Purpose must be one of: {", ".join(allowed_purposes)}')
        return v

    @validator('amount')
    def validate_amount(cls, v):
        if v < Decimal('1.0'):
            raise ValueError('Amount must be at least ₹1')
        if v > Decimal('100000.0'):
            raise ValueError('Amount cannot exceed ₹1,00,000')
        return v


class CreateSubscriptionRequest(BaseModel):
    """Create subscription request schema"""
    tenant_id: UUID = Field(..., description="Tenant ID")
    booking_id: UUID = Field(..., description="Booking ID")
    plan_id: str = Field(..., description="Razorpay plan ID")
    customer_notify: bool = Field(default=True, description="Notify customer")
    total_count: Optional[int] = Field(None, description="Total subscription cycles")


class PaymentIntentResponse(BaseModel):
    """Payment intent response schema"""
    id: UUID
    razorpay_order_id: Optional[str]
    amount: Decimal
    currency: str
    purpose: str
    status: PaymentStatus
    upi_intent_url: Optional[str] = None
    razorpay_key_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment response schema"""
    id: UUID
    razorpay_payment_id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: Optional[PaymentMethod]
    fee: Optional[Decimal]
    receipt_url: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription response schema"""
    id: UUID
    razorpay_subscription_id: str
    tenant_id: UUID
    booking_id: UUID
    amount: Decimal
    status: SubscriptionStatus
    start_date: datetime
    next_charge_at: Optional[datetime] = None
    paid_count: int = 0
    remaining_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookResponse(BaseModel):
    """Webhook response schema"""
    status: str = Field(default="success")
    message: str = Field(default="Webhook processed successfully")


class PaymentVerificationRequest(BaseModel):
    """Payment verification request from frontend"""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class RefundRequest(BaseModel):
    """Refund request schema"""
    payment_id: UUID
    amount: Optional[Decimal] = Field(None, description="Partial refund amount")
    reason: Optional[str] = Field(None, description="Refund reason")


class RefundResponse(BaseModel):
    """Refund response schema"""
    id: UUID
    razorpay_refund_id: str
    amount: Decimal
    status: str
    reason: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class LedgerEntryResponse(BaseModel):
    """Ledger entry response schema"""
    id: UUID
    tenant_id: UUID
    account: str
    debit: Optional[Decimal]
    credit: Optional[Decimal]
    description: str
    reference_type: str
    reference_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentSummaryResponse(BaseModel):
    """Payment summary for tenant dashboard"""
    total_paid: Decimal
    pending_amount: Decimal
    last_payment_date: Optional[datetime]
    next_due_date: Optional[datetime]
    active_subscriptions: int
    recent_payments: list[PaymentResponse]


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== Dummy Rent Payment (no gateway) =====

class CreateDummyRentPaymentRequest(BaseModel):
    """Create a dummy rent payment without gateway integration"""
    tenant_id: UUID = Field(..., description="Tenant ID")
    room_no: str = Field(..., max_length=50, description="Room number")
    amount: Decimal = Field(..., gt=0, description="Rent amount (₹)")
    due_date: Optional[datetime] = Field(None, description="Payment due date")
    payment_date: Optional[datetime] = Field(None, description="Payment date (defaults to now)")


class RentPaymentResponse(BaseModel):
    """Unified rent payment response"""
    id: UUID
    payment_intent_id: UUID
    tenant_id: UUID
    room_no: str
    amount: Decimal
    status: PaymentStatus
    due_date: Optional[datetime]
    payment_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True