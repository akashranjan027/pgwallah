"""
Mess Coupons endpoints

Uses PostgreSQL for persistence via SQLAlchemy models.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import MealCoupon, TimeSlot as TimeSlotEnum

router = APIRouter()

TimeSlot = Literal["breakfast", "lunch", "snacks", "dinner"]


# Pydantic schemas
class CouponResponse(BaseModel):
    id: str
    tenant_id: str
    slot: str
    for_date: date
    issued_at: datetime
    used_at: Optional[datetime] = None
    is_used: bool = False

    class Config:
        from_attributes = True


class IssueCouponsPayload(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID (UUID as string)")
    for_date: Optional[date] = Field(default=None, description="Date for which coupons are issued (default: today)")
    slots: Optional[List[TimeSlot]] = Field(
        default=None,
        description='Subset of ["breakfast", "lunch", "snacks", "dinner"]; default: all four',
    )


class RedeemPayload(BaseModel):
    coupon_id: str


def _coupon_to_dict(coupon: MealCoupon) -> dict:
    """Convert SQLAlchemy model to dict for response."""
    return {
        "id": str(coupon.id),
        "tenant_id": str(coupon.tenant_id),
        "slot": coupon.slot.value if hasattr(coupon.slot, 'value') else str(coupon.slot),
        "for_date": coupon.for_date,
        "issued_at": coupon.created_at,
        "used_at": coupon.used_at,
        "is_used": coupon.is_used,
    }


@router.get("/coupons")
async def list_coupons(
    tenant_id: Optional[str] = Query(default=None, description="Filter by tenant_id"),
    for_date: Optional[date] = Query(default=None, description="Filter by date"),
    include_used: bool = Query(default=False, description="Include used coupons"),
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """List (optionally filtered) coupons."""
    query = select(MealCoupon)
    
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
            query = query.where(MealCoupon.tenant_id == tenant_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant_id format")
    
    if for_date:
        query = query.where(MealCoupon.for_date == for_date)
    
    if not include_used:
        query = query.where(MealCoupon.is_used.is_(False))
    
    # Sort by date, then slot
    query = query.order_by(MealCoupon.for_date, MealCoupon.slot)
    
    result = await db.execute(query)
    coupons = result.scalars().all()
    
    return [_coupon_to_dict(c) for c in coupons]


@router.post("/coupons", status_code=status.HTTP_201_CREATED)
async def issue_coupons(
    payload: IssueCouponsPayload,
    db: AsyncSession = Depends(get_db)
) -> List[dict]:
    """
    Issue daily coupons for tenant. By default issues all 4 meal slots for the given date.
    Does not duplicate existing coupons for the same tenant/date/slot.
    """
    try:
        tenant_uuid = UUID(payload.tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant_id format")
    
    target_date = payload.for_date or date.today()
    slots = payload.slots or ["breakfast", "lunch", "snacks", "dinner"]

    created: List[dict] = []
    
    for slot_name in slots:
        slot_enum = TimeSlotEnum(slot_name)
        
        # Check if coupon already exists
        existing = await db.execute(
            select(MealCoupon).where(
                and_(
                    MealCoupon.tenant_id == tenant_uuid,
                    MealCoupon.for_date == target_date,
                    MealCoupon.slot == slot_enum
                )
            )
        )
        if existing.scalar_one_or_none():
            # Skip duplicate
            continue
        
        coupon = MealCoupon(
            tenant_id=tenant_uuid,
            for_date=target_date,
            slot=slot_enum,
            is_used=False,
        )
        db.add(coupon)
        await db.flush()
        created.append(_coupon_to_dict(coupon))
    
    await db.commit()
    return created


@router.post("/coupons/redeem")
async def redeem_coupon(
    payload: RedeemPayload,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Mark a coupon as used (redeemed)."""
    try:
        coupon_uuid = UUID(payload.coupon_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid coupon_id format")
    
    result = await db.execute(select(MealCoupon).where(MealCoupon.id == coupon_uuid))
    coupon = result.scalar_one_or_none()
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if coupon.is_used:
        raise HTTPException(status_code=400, detail="Coupon already used")
    
    coupon.is_used = True
    coupon.used_at = datetime.utcnow()
    await db.commit()
    await db.refresh(coupon)
    
    return _coupon_to_dict(coupon)


@router.get("/coupons/validate")
async def validate_coupon(
    coupon_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate an existing coupon ID; returns basic details if valid and unused."""
    try:
        coupon_uuid = UUID(coupon_id)
    except ValueError:
        return {"valid": False, "reason": "invalid_format"}
    
    result = await db.execute(select(MealCoupon).where(MealCoupon.id == coupon_uuid))
    coupon = result.scalar_one_or_none()
    
    if not coupon:
        return {"valid": False, "reason": "not_found"}
    if coupon.is_used:
        return {"valid": False, "reason": "already_used"}
    
    return {
        "valid": True,
        "coupon": _coupon_to_dict(coupon),
    }


@router.get("/coupons/{coupon_id}")
async def get_coupon(
    coupon_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get a specific coupon by ID."""
    try:
        coupon_uuid = UUID(coupon_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid coupon_id format")
    
    result = await db.execute(select(MealCoupon).where(MealCoupon.id == coupon_uuid))
    coupon = result.scalar_one_or_none()
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    return _coupon_to_dict(coupon)