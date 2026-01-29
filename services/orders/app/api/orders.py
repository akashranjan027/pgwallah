"""
Food ordering API endpoints for in-house mess
"""
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

import httpx
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import and_, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderSequence, OrderStatus, PaymentStatus
from app.schemas.order import (
    CreateOrderRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
    KitchenOrderResponse,
    OrderSummaryResponse,
)
from app.utils.events import publish_order_event
from app.utils.menu import get_menu_items_from_mess_service

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create new food order from mess menu"""
    
    logger.info(
        "Creating food order",
        tenant_id=str(request.tenant_id),
        items_count=len(request.items),
    )

    # Get menu items from mess service to validate and get prices
    menu_items = await get_menu_items_from_mess_service()
    menu_lookup = {item["id"]: item for item in menu_items}

    # Validate items and calculate totals
    order_items = []
    subtotal = Decimal('0.00')
    tax_amount = Decimal('0.00')

    for item_request in request.items:
        menu_item = menu_lookup.get(str(item_request.menu_item_id))
        if not menu_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Menu item {item_request.menu_item_id} not found"
            )

        if not menu_item.get("is_available", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Menu item {menu_item['name']} is not available"
            )

        unit_price = Decimal(str(menu_item["price"]))
        line_total = unit_price * item_request.quantity
        
        # Calculate tax (5% GST for food items)
        tax_rate = Decimal('5.00')
        item_tax = line_total * tax_rate / 100
        
        order_item = OrderItem(
            menu_item_id=item_request.menu_item_id,
            name=menu_item["name"],
            description=menu_item.get("description"),
            quantity=item_request.quantity,
            unit_price=unit_price,
            line_total=line_total,
            tax_rate=tax_rate,
            tax_amount=item_tax,
            customizations=json.dumps(item_request.customizations) if item_request.customizations else None,
            special_instructions=item_request.special_instructions,
        )
        
        order_items.append(order_item)
        subtotal += line_total
        tax_amount += item_tax

    # Generate order number
    # Use a normalized midnight UTC datetime to match DateTime column type
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    stmt = select(OrderSequence).where(OrderSequence.date == today)
    result = await db.execute(stmt)
    sequence = result.scalar_one_or_none()
    
    if not sequence:
        sequence = OrderSequence(date=today)
        db.add(sequence)
        await db.flush()
    
    order_number = sequence.generate_order_number()

    # Calculate final amounts
    delivery_charge = Decimal('0.00')  # Free delivery within PG
    total_amount = subtotal + tax_amount + delivery_charge

    # Apply coupon discount if provided
    coupon_discount = Decimal('0.00')
    if request.coupon_id:
        # Validate coupon with mess service
        coupon_valid = False
        if settings.MESS_SERVICE_URL:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(
                        f"{settings.MESS_SERVICE_URL}/api/coupons/validate",
                        params={"coupon_id": request.coupon_id}
                    )
                    if response.status_code == 200:
                        validation_result = response.json()
                        coupon_valid = validation_result.get("valid", False)
                        if not coupon_valid:
                            reason = validation_result.get("reason", "unknown")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid coupon: {reason}"
                            )
                        # Mark coupon as used
                        await client.post(
                            f"{settings.MESS_SERVICE_URL}/api/coupons/redeem",
                            json={"coupon_id": request.coupon_id}
                        )
                        coupon_discount = min(subtotal, total_amount)  # Can use full amount as coupon
                        logger.info("Coupon validated and redeemed", coupon_id=request.coupon_id)
            except httpx.RequestError as e:
                logger.warning("Failed to validate coupon", error=str(e))
                # Only allow fallback in development mode with explicit config
                if settings.ALLOW_COUPON_FALLBACK:
                    logger.warning("Coupon validation failed, using fallback (ALLOW_COUPON_FALLBACK=true)")
                    coupon_discount = min(subtotal, total_amount)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Coupon service unavailable. Please try again later."
                    )
        else:
            # No mess service configured; accept coupon only in dev mode
            if settings.ALLOW_COUPON_FALLBACK:
                logger.warning("No mess service configured, using coupon fallback (ALLOW_COUPON_FALLBACK=true)")
                coupon_discount = min(subtotal, total_amount)
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Coupon service not configured"
                )

    final_amount = total_amount - coupon_discount

    # Create order
    order = Order(
        order_number=order_number,
        tenant_id=request.tenant_id,
        subtotal=subtotal,
        tax_amount=tax_amount,
        delivery_charge=delivery_charge,
        total_amount=final_amount,
        coupon_id=request.coupon_id,
        coupon_discount=coupon_discount,
        delivery_address=request.delivery_address,
        delivery_instructions=request.delivery_instructions,
        customer_notes=request.customer_notes,
        payment_status=PaymentStatus.COUPON_USED if request.coupon_id else PaymentStatus.PENDING,
    )

    # Add items to order
    for order_item in order_items:
        order_item.order = order
        db.add(order_item)

    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Publish order event
    background_tasks.add_task(
        publish_order_event,
        "order.placed",
        {
            "order_id": str(order.id),
            "tenant_id": str(order.tenant_id),
            "order_number": order.order_number,
            "total_amount": float(order.total_amount),
            "items_count": len(order.items),
            "payment_status": order.payment_status.value,
        },
    )

    logger.info(
        "Food order created successfully",
        order_id=str(order.id),
        order_number=order.order_number,
        total_amount=order.total_amount,
    )

    return OrderResponse.model_validate(order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get order details"""
    
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return OrderResponse.model_validate(order)


@router.get("/", response_model=List[OrderResponse])
@router.get("", response_model=List[OrderResponse])
async def list_orders(
    tenant_id: Optional[uuid.UUID] = None,
    status: Optional[OrderStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List orders with filtering"""
    
    stmt = select(Order)
    
    if tenant_id:
        stmt = stmt.where(Order.tenant_id == tenant_id)
    
    if status:
        stmt = stmt.where(Order.status == status)
    
    stmt = stmt.order_by(Order.created_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return [OrderResponse.model_validate(order) for order in orders]


@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Cancel an order"""
    
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if not order.is_cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order cannot be cancelled in {order.status} status"
        )

    # Update order status
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = datetime.utcnow()
    order.cancellation_reason = reason

    await db.commit()

    # Publish cancellation event
    background_tasks.add_task(
        publish_order_event,
        "order.cancelled",
        {
            "order_id": str(order.id),
            "tenant_id": str(order.tenant_id),
            "order_number": order.order_number,
            "reason": reason,
        },
    )

    logger.info(
        "Order cancelled",
        order_id=str(order.id),
        order_number=order.order_number,
        reason=reason,
    )

    return {"message": "Order cancelled successfully"}


@router.get("/kitchen/orders", response_model=List[KitchenOrderResponse])
async def get_kitchen_orders(
    status: Optional[OrderStatus] = None,
    station: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get orders for kitchen staff console"""
    
    stmt = select(Order)
    
    # Default to active orders for kitchen
    if status is None:
        stmt = stmt.where(
            Order.status.in_([
                OrderStatus.CONFIRMED,
                OrderStatus.PREPARING,
                OrderStatus.READY
            ])
        )
    else:
        stmt = stmt.where(Order.status == status)
    
    if station:
        stmt = stmt.where(Order.assigned_station == station)
    
    stmt = stmt.order_by(Order.order_time.asc())
    
    result = await db.execute(stmt)
    orders = result.scalars().all()

    kitchen_orders = []
    for order in orders:
        kitchen_orders.append(KitchenOrderResponse(
            id=order.id,
            order_number=order.order_number,
            tenant_id=order.tenant_id,
            status=order.status,
            items=order.items,
            total_amount=order.total_amount,
            order_time=order.order_time,
            estimated_ready_time=order.estimated_ready_time,
            assigned_station=order.assigned_station,
            customer_notes=order.customer_notes,
            kitchen_notes=order.kitchen_notes,
        ))

    return kitchen_orders


@router.put("/{order_id}/kitchen", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    request: OrderStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Update order status from kitchen console"""
    
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Update status and timestamps
    old_status = order.status
    order.status = request.status
    
    now = datetime.utcnow()
    
    if request.status == OrderStatus.CONFIRMED:
        order.confirmed_at = now
        # Estimate preparation time
        order.estimated_preparation_time = request.estimated_prep_minutes or 15
        order.estimated_ready_time = now + timedelta(minutes=order.estimated_preparation_time)
        
    elif request.status == OrderStatus.PREPARING:
        order.preparation_started_at = now
        
    elif request.status == OrderStatus.READY:
        order.ready_at = now
        
    elif request.status == OrderStatus.DELIVERED:
        order.delivered_at = now

    # Update kitchen notes and station assignment
    if request.kitchen_notes:
        order.kitchen_notes = request.kitchen_notes
    
    if request.assigned_station:
        order.assigned_station = request.assigned_station

    await db.commit()

    # Publish status update event
    background_tasks.add_task(
        publish_order_event,
        f"order.{request.status.value}",
        {
            "order_id": str(order.id),
            "tenant_id": str(order.tenant_id),
            "order_number": order.order_number,
            "old_status": old_status.value,
            "new_status": request.status.value,
            "estimated_ready_time": order.estimated_ready_time.isoformat() if order.estimated_ready_time else None,
        },
    )

    logger.info(
        "Order status updated",
        order_id=str(order.id),
        old_status=old_status.value,
        new_status=request.status.value,
    )

    return OrderResponse.model_validate(order)


@router.get("/tenant/{tenant_id}/summary", response_model=OrderSummaryResponse)
async def get_tenant_order_summary(
    tenant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get order summary for tenant dashboard"""
    
    # Get recent orders
    stmt = (
        select(Order)
        .where(Order.tenant_id == tenant_id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    recent_orders = result.scalars().all()

    # Count orders by status (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    total_spent_stmt = (
        select(func.sum(Order.total_amount))
        .where(
            and_(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.DELIVERED,
                Order.created_at >= thirty_days_ago
            )
        )
    )
    result = await db.execute(total_spent_stmt)
    total_spent = result.scalar() or Decimal('0.00')

    # Active orders count
    active_orders_stmt = (
        select(func.count(Order.id))
        .where(
            and_(
                Order.tenant_id == tenant_id,
                Order.status.in_([
                    OrderStatus.PENDING,
                    OrderStatus.CONFIRMED,
                    OrderStatus.PREPARING,
                    OrderStatus.READY
                ])
            )
        )
    )
    result = await db.execute(active_orders_stmt)
    active_orders_count = result.scalar() or 0

    return OrderSummaryResponse(
        recent_orders=[OrderResponse.model_validate(order) for order in recent_orders],
        total_spent_30_days=total_spent,
        active_orders_count=active_orders_count,
        last_order_date=recent_orders[0].created_at if recent_orders else None,
    )