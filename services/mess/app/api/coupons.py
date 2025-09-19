"""
Mess Coupons endpoints

Note: For development this uses in-memory stores. Replace with DB models in production.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Dict, List, Optional, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter()

TimeSlot = Literal["breakfast", "lunch", "snacks", "dinner"]


class Coupon(BaseModel):
    id: str
    tenant_id: str
    slot: TimeSlot
    for_date: date
    issued_at: datetime
    used_at: Optional[datetime] = None
    is_used: bool = False


# In-memory coupon store: coupon_id -> Coupon
COUPONS: Dict[str, Coupon] = {}


class IssueCouponsPayload(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID (UUID as string)")
    for_date: Optional[date] = Field(default=None, description="Date for which coupons are issued (default: today)")
    slots: Optional[List[TimeSlot]] = Field(
        default=None,
        description='Subset of ["breakfast", "lunch", "snacks", "dinner"]; default: all four',
    )


@router.get("/coupons")
async def list_coupons(
    tenant_id: Optional[str] = Query(default=None, description="Filter by tenant_id"),
    for_date: Optional[date] = Query(default=None, description="Filter by date"),
    include_used: bool = Query(default=False, description="Include used coupons"),
) -> List[Coupon]:
    """List (optionally filtered) coupons."""
    results: List[Coupon] = []
    for c in COUPONS.values():
        if tenant_id and c.tenant_id != tenant_id:
            continue
        if for_date and c.for_date != for_date:
            continue
        if (not include_used) and c.is_used:
            continue
        results.append(c)
    # Sort by date, then slot
    order_map = {"breakfast": 1, "lunch": 2, "snacks": 3, "dinner": 4}
    results.sort(key=lambda x: (x.for_date, order_map.get(x.slot, 99)))
    return results


@router.post("/coupons", status_code=status.HTTP_201_CREATED)
async def issue_coupons(payload: IssueCouponsPayload) -> List[Coupon]:
    """
    Issue daily coupons for tenant. By default issues all 4 meal slots for the given date.
    Does not duplicate existing coupons for the same tenant/date/slot.
    """
    target_date = payload.for_date or date.today()
    slots = payload.slots or ["breakfast", "lunch", "snacks", "dinner"]

    created: List[Coupon] = []
    # Avoid duplicates for same tenant/date/slot
    existing = {
        (c.tenant_id, c.for_date.isoformat(), c.slot): c
        for c in COUPONS.values()
    }
    for slot in slots:
        key = (payload.tenant_id, target_date.isoformat(), slot)
        if key in existing:
            # skip duplicate
            continue
        coupon = Coupon(
            id=str(uuid.uuid4()),
            tenant_id=payload.tenant_id,
            slot=slot,  # type: ignore[arg-type]
            for_date=target_date,
            issued_at=datetime.utcnow(),
            is_used=False,
        )
        COUPONS[coupon.id] = coupon
        created.append(coupon)
    return created


class RedeemPayload(BaseModel):
    coupon_id: str


@router.post("/coupons/redeem")
async def redeem_coupon(payload: RedeemPayload) -> Coupon:
    """Mark a coupon as used (redeemed)."""
    coupon = COUPONS.get(payload.coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if coupon.is_used:
        raise HTTPException(status_code=400, detail="Coupon already used")
    coupon.is_used = True
    coupon.used_at = datetime.utcnow()
    COUPONS[coupon.id] = coupon
    return coupon


@router.get("/coupons/validate")
async def validate_coupon(coupon_id: str):
    """Validate an existing coupon ID; returns basic details if valid and unused."""
    coupon = COUPONS.get(coupon_id)
    if not coupon:
        return {"valid": False, "reason": "not_found"}
    if coupon.is_used:
        return {"valid": False, "reason": "already_used"}
    # Allow validating only for today or any date? Here we allow any date (can add policy later)
    return {
        "valid": True,
        "coupon": coupon,
    }