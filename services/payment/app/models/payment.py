"""
Payment and billing database models
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Numeric, String, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    CREATED = "created"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    UPI = "upi"
    CARD = "card"
    NET_BANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration"""
    CREATED = "created"
    AUTHENTICATED = "authenticated"
    ACTIVE = "active"
    PAUSED = "paused"
    HALTED = "halted"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentIntent(Base):
    """Payment intent model for rent and other payments"""
    
    __tablename__ = "payment_intents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True
    )
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False
    )
    
    purpose: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )  # rent, deposit, mess, etc.
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.CREATED,
        nullable=False,
        index=True
    )
    
    # 'metadata' is a reserved attribute in SQLAlchemy declarative models.
    # Keep the DB column name as "metadata" but use a different Python attribute.
    extra_metadata: Mapped[Optional[str]] = mapped_column(
        "metadata",
        Text,  # JSON string for additional data
        nullable=True
    )
    
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<PaymentIntent {self.id} {self.purpose} ₹{self.amount}>"


class Payment(Base):
    """Payment record model for completed transactions"""
    
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    razorpay_payment_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    
    razorpay_order_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False
    )
    
    razorpay_signature: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    payment_intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False
    )
    
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        nullable=False,
        index=True
    )
    
    method: Mapped[Optional[PaymentMethod]] = mapped_column(
        SQLEnum(PaymentMethod),
        nullable=True
    )
    
    fee: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True
    )
    
    tax: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True
    )
    
    razorpay_webhook_payload: Mapped[Optional[str]] = mapped_column(
        Text,  # Store complete webhook for audit
        nullable=True
    )
    
    receipt_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Payment {self.razorpay_payment_id} ₹{self.amount} {self.status}>"


class Subscription(Base):
    """Subscription model for recurring rent payments"""
    
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    razorpay_subscription_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    
    razorpay_plan_id: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False
    )
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False
    )
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.CREATED,
        nullable=False,
        index=True
    )
    
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    total_count: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )
    
    paid_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    remaining_count: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )
    
    current_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    current_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    next_charge_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.razorpay_subscription_id} ₹{self.amount}/month {self.status}>"


class Refund(Base):
    """Refund model for payment reversals"""
    
    __tablename__ = "refunds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    razorpay_refund_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False
    )
    
    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    receipt_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Refund {self.razorpay_refund_id} ₹{self.amount}>"


class AdvancePayment(Base):
   """Advance payment record (dummy/no-gateway for now)"""
   __tablename__ = "advance_payments"

   id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       primary_key=True,
       default=uuid.uuid4,
       index=True,
   )

   tenant_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       nullable=False,
       index=True,
   )

   pg_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       ForeignKey("pgs.id", ondelete="CASCADE"),
       nullable=False,
       index=True,
   )

   amount: Mapped[Decimal] = mapped_column(
       Numeric(precision=10, scale=2),
       nullable=False,
   )

   payment_date: Mapped[Optional[datetime]] = mapped_column(
       DateTime(timezone=True),
       nullable=True,
   )

   notes: Mapped[Optional[str]] = mapped_column(
       String(500),
       nullable=True,
   )

   created_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True),
       server_default=func.now(),
       nullable=False,
   )

   def __repr__(self) -> str:
       return f"<AdvancePayment pg={self.pg_id} tenant={self.tenant_id} ₹{self.amount}>"


class Ledger(Base):
    """Ledger entries for double-entry bookkeeping"""
    
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    transaction_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    
    account: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )  # rent_receivable, security_deposit, mess_charges, etc.
    
    debit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True
    )
    
    credit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=True
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    reference_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # payment, booking, invoice, etc.
    
    reference_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        amount = f"₹{self.debit}" if self.debit else f"₹{self.credit}"
        return f"<Ledger {self.account} {amount}>"


class RentPayment(Base):
   """Simple rent payment record (dummy/no-gateway)"""

   __tablename__ = "rent_payments"

   id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       primary_key=True,
       default=uuid.uuid4,
       index=True,
   )

   payment_intent_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       nullable=False,
       index=True,
   )

   tenant_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True),
       nullable=False,
       index=True,
   )

   room_no: Mapped[str] = mapped_column(
       String(50),
       nullable=False,
       index=True,
   )

   amount: Mapped[Decimal] = mapped_column(
       Numeric(precision=10, scale=2),
       nullable=False,
   )

   status: Mapped[PaymentStatus] = mapped_column(
       SQLEnum(PaymentStatus),
       default=PaymentStatus.CAPTURED,
       nullable=False,
       index=True,
   )

   due_date: Mapped[Optional[datetime]] = mapped_column(
       DateTime(timezone=True),
       nullable=True,
   )

   payment_date: Mapped[Optional[datetime]] = mapped_column(
       DateTime(timezone=True),
       nullable=True,
   )

   created_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True),
       server_default=func.now(),
       nullable=False,
   )

   updated_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True),
       server_default=func.now(),
       onupdate=func.now(),
       nullable=False,
   )

   def __repr__(self) -> str:
       return f"<RentPayment room {self.room_no} ₹{self.amount} {self.status}>"


# =========================
# PG/Property and mapping
# =========================

class PG(Base):
   """Paying Guest (PG) entity"""
   __tablename__ = "pgs"

   id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
   )
   name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
   address_line1: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
   address_line2: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
   city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
   state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
   pincode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

   created_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True), server_default=func.now(), nullable=False
   )
   updated_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
   )

   def __repr__(self) -> str:
       return f"<PG {self.name}>"


class PGAdmin(Base):
   """Mapping of a User (Auth service user_id) as admin for a PG"""
   __tablename__ = "pg_admins"

   id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
   )
   pg_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), ForeignKey("pgs.id", ondelete="CASCADE"), nullable=False, index=True
   )
   user_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), nullable=False, index=True
   )  # Auth service user ID (admin)

   role: Mapped[str] = mapped_column(
       String(50), nullable=False, default="admin"
   )  # future: owner/manager/admin

   created_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True), server_default=func.now(), nullable=False
   )

   def __repr__(self) -> str:
       return f"<PGAdmin pg={self.pg_id} user={self.user_id} role={self.role}>"


class PGMembership(Base):
   """Maps tenant to a PG with room/rent details"""
   __tablename__ = "pg_memberships"

   id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
   )
   pg_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), ForeignKey("pgs.id", ondelete="CASCADE"), nullable=False, index=True
   )
   tenant_id: Mapped[uuid.UUID] = mapped_column(
       UUID(as_uuid=True), nullable=False, index=True
   )
   room_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

   rent_amount: Mapped[Decimal] = mapped_column(
       Numeric(precision=10, scale=2), nullable=False
   )
   start_date: Mapped[Optional[datetime]] = mapped_column(
       DateTime(timezone=True), nullable=True
   )
   end_date: Mapped[Optional[datetime]] = mapped_column(
       DateTime(timezone=True), nullable=True
   )
   active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

   created_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True), server_default=func.now(), nullable=False
   )
   updated_at: Mapped[datetime] = mapped_column(
       DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
   )

   def __repr__(self) -> str:
       return f"<PGMembership pg={self.pg_id} tenant={self.tenant_id} room={self.room_no} active={self.active}>"