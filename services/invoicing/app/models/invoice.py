"""
Invoice and billing database models with GST support
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InvoiceStatus(str, Enum):
    """Invoice status enumeration"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceType(str, Enum):
    """Invoice type enumeration"""
    RENT = "rent"
    MESS = "mess"
    COMBINED = "combined"
    DEPOSIT_REFUND = "deposit_refund"


class TaxType(str, Enum):
    """Tax type enumeration for GST"""
    CGST = "cgst"  # Central GST
    SGST = "sgst"  # State GST
    IGST = "igst"  # Integrated GST
    EXEMPT = "exempt"  # Tax exempt (rent in most cases)


class Invoice(Base):
    """Invoice model with GST compliance for Indian market"""
    
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    invoice_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    booking_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    invoice_type: Mapped[InvoiceType] = mapped_column(
        SQLEnum(InvoiceType),
        nullable=False,
        index=True
    )
    
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus),
        default=InvoiceStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Invoice period
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    # Financial details
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    # GST Details
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15),  # GST Identification Number
        nullable=True
    )
    
    place_of_supply: Mapped[str] = mapped_column(
        String(100),
        default="Karnataka",  # Default for Bengaluru
        nullable=False
    )
    
    # Dates
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    paid_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # File storage
    pdf_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Email tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    reminder_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    last_reminder_sent: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Notes and metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
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

    # Relationships
    items: Mapped[list["InvoiceItem"]] = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ₹{self.total_amount} {self.status}>"


class InvoiceItem(Base):
    """Invoice line item model"""
    
    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('1.00'),
        nullable=False
    )
    
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    # Tax details
    tax_type: Mapped[TaxType] = mapped_column(
        SQLEnum(TaxType),
        default=TaxType.EXEMPT,
        nullable=False
    )
    
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    # HSN/SAC code for GST
    hsn_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    # Reference to source data
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )  # payment, booking, mess_charge, etc.
    
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")

    def __repr__(self) -> str:
        return f"<InvoiceItem {self.description} ₹{self.line_total}>"


class InvoiceSequence(Base):
    """Invoice numbering sequence per financial year"""
    
    __tablename__ = "invoice_sequences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    financial_year: Mapped[str] = mapped_column(
        String(10),  # e.g., "2024-25"
        unique=True,
        index=True,
        nullable=False
    )
    
    current_number: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )
    
    prefix: Mapped[str] = mapped_column(
        String(10),
        default="INV",
        nullable=False
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

    def generate_invoice_number(self) -> str:
        """Generate next invoice number"""
        self.current_number += 1
        return f"{self.prefix}/{self.financial_year}/{self.current_number:06d}"

    def __repr__(self) -> str:
        return f"<InvoiceSequence {self.financial_year} #{self.current_number}>"


class TaxSlab(Base):
    """Tax rate configuration for different items"""
    
    __tablename__ = "tax_slabs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )
    
    tax_type: Mapped[TaxType] = mapped_column(
        SQLEnum(TaxType),
        nullable=False
    )
    
    rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        nullable=False
    )
    
    hsn_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<TaxSlab {self.name} {self.rate}% {self.tax_type}>"