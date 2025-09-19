"""
Pydantic schemas for Orders service
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Any

from pydantic import BaseModel, Field
from app.models.order import OrderStatus


# Request Schemas

class CreateOrderItemRequest(BaseModel):
    """Line item from menu for placing an order"""
    menu_item_id: uuid.UUID = Field(..., description="ID of the menu item from Mess service")
    quantity: int = Field(..., ge=1, le=20, description="Quantity of the item")
    customizations: Optional[dict[str, Any]] = Field(
        default=None, description="Customization options as free-form JSON"
    )
    special_instructions: Optional[str] = Field(
        default=None, max_length=500, description="Free text instructions"
    )


class CreateOrderRequest(BaseModel):
    """Create order payload"""
    tenant_id: uuid.UUID = Field(..., description="Tenant placing the order")
    items: List[CreateOrderItemRequest] = Field(..., min_items=1, max_items=50)
    coupon_id: Optional[uuid.UUID] = Field(default=None, description="Applied mess coupon, if any")
    delivery_address: Optional[str] = Field(default=None, max_length=500)
    delivery_instructions: Optional[str] = Field(default=None, max_length=500)
    customer_notes: Optional[str] = Field(default=None, max_length=500)


class OrderStatusUpdateRequest(BaseModel):
    """Kitchen/staff status update request"""
    status: OrderStatus = Field(..., description="New status for the order")
    estimated_prep_minutes: Optional[int] = Field(default=None, ge=1, le=240)
    kitchen_notes: Optional[str] = Field(default=None, max_length=500)
    assigned_station: Optional[str] = Field(default=None, max_length=100)


# Response Schemas

class OrderItemResponse(BaseModel):
    """Order item line for responses"""
    id: uuid.UUID
    order_id: uuid.UUID
    menu_item_id: uuid.UUID
    name: str
    description: Optional[str]
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    customizations: Optional[str]
    special_instructions: Optional[str]
    tax_rate: Decimal
    tax_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order details response"""
    id: uuid.UUID
    order_number: str
    tenant_id: uuid.UUID
    status: OrderStatus
    payment_status: str
    subtotal: Decimal
    tax_amount: Decimal
    delivery_charge: Decimal
    total_amount: Decimal
    coupon_id: Optional[uuid.UUID]
    coupon_discount: Decimal
    payment_intent_id: Optional[uuid.UUID]
    delivery_address: Optional[str]
    delivery_instructions: Optional[str]
    order_time: datetime
    confirmed_at: Optional[datetime]
    preparation_started_at: Optional[datetime]
    ready_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]
    estimated_preparation_time: Optional[int]
    estimated_ready_time: Optional[datetime]
    assigned_station: Optional[str]
    assigned_staff_id: Optional[uuid.UUID]
    customer_notes: Optional[str]
    kitchen_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class KitchenOrderResponse(BaseModel):
    """Slim order view for kitchen consoles"""
    id: uuid.UUID
    order_number: str
    tenant_id: uuid.UUID
    status: OrderStatus
    items: List[OrderItemResponse]
    total_amount: Decimal
    order_time: datetime
    estimated_ready_time: Optional[datetime]
    assigned_station: Optional[str]
    customer_notes: Optional[str]
    kitchen_notes: Optional[str]


class OrderSummaryResponse(BaseModel):
    """Summary stats for a tenant's dashboard"""
    recent_orders: List[OrderResponse]
    total_spent_30_days: Decimal
    active_orders_count: int
    last_order_date: Optional[datetime]