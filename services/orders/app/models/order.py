"""
Food order database models for in-house mess ordering
"""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, Numeric, String, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status for orders"""
    PENDING = "pending"
    PAID = "paid"
    COUPON_USED = "coupon_used"
    REFUNDED = "refunded"


class Order(Base):
    """Food order model for mess ordering"""
    
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    order_number: Mapped[str] = mapped_column(
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
    
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )
    
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Order details
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    delivery_charge: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False
    )
    
    # Coupon usage
    coupon_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    coupon_discount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    # Payment reference
    payment_intent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Delivery details
    delivery_address: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    delivery_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Timestamps
    order_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    preparation_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    ready_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Estimated times
    estimated_preparation_time: Mapped[Optional[int]] = mapped_column(
        Integer,  # in minutes
        nullable=True
    )
    
    estimated_ready_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Staff assignment
    assigned_station: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    
    assigned_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    # Notes
    customer_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    kitchen_notes: Mapped[Optional[str]] = mapped_column(
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
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number} ₹{self.total_amount} {self.status}>"

    @property
    def is_cancellable(self) -> bool:
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    @property
    def is_modifiable(self) -> bool:
        """Check if order can be modified"""
        return self.status == OrderStatus.PENDING


class OrderItem(Base):
    """Order line item model"""
    
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    quantity: Mapped[int] = mapped_column(
        Integer,
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
    
    # Customizations
    customizations: Mapped[Optional[str]] = mapped_column(
        Text,  # JSON string for customization options
        nullable=True
    )
    
    special_instructions: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Tax details (for mess items)
    tax_rate: Mapped[Decimal] = mapped_column(
        Numeric(precision=5, scale=2),
        default=Decimal('5.00'),  # 5% GST for food items
        nullable=False
    )
    
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItem {self.name} x{self.quantity} ₹{self.line_total}>"


class KitchenStation(Base):
    """Kitchen station model for order preparation"""
    
    __tablename__ = "kitchen_stations"

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
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    
    # Capacity management
    max_concurrent_orders: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False
    )
    
    average_prep_time_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
        nullable=False
    )
    
    # Staff assignment
    assigned_staff_ids: Mapped[Optional[str]] = mapped_column(
        Text,  # JSON array of staff IDs
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
        return f"<KitchenStation {self.name}>"


class OrderSequence(Base):
    """Order numbering sequence per day"""
    
    __tablename__ = "order_sequences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        unique=True,
        index=True,
        nullable=False
    )
    
    current_number: Mapped[int] = mapped_column(
        default=0,
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

    def generate_order_number(self) -> str:
        """Generate next order number for the day"""
        self.current_number += 1
        date_str = self.date.strftime("%Y%m%d")
        return f"ORD{date_str}{self.current_number:04d}"

    def __repr__(self) -> str:
        return f"<OrderSequence {self.date.strftime('%Y-%m-%d')} #{self.current_number}>"