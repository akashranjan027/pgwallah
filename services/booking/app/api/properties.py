"""
Properties API endpoints
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Property
from app.schemas import (
    PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse
)

router = APIRouter()


@router.get("/properties", response_model=PropertyListResponse)
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all properties with optional filters"""
    query = select(Property).where(Property.is_active == is_active)
    
    if city:
        query = query.where(Property.city.ilike(f"%{city}%"))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get items
    query = query.offset(skip).limit(limit).order_by(Property.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PropertyListResponse(items=items, total=total or 0)


@router.post("/properties", response_model=PropertyResponse, status_code=201)
async def create_property(
    data: PropertyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new property (admin only)"""
    property_obj = Property(
        name=data.name,
        address=data.address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        property_type=data.property_type,
        description=data.description,
        amenities=data.amenities,
        contact_phone=data.contact_phone,
        contact_email=data.contact_email,
        owner_id=data.owner_id,
    )
    
    db.add(property_obj)
    await db.commit()
    await db.refresh(property_obj)
    
    return property_obj


@router.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get property by ID"""
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return property_obj


@router.put("/properties/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    data: PropertyUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update property (admin only)"""
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_obj, field, value)
    
    await db.commit()
    await db.refresh(property_obj)
    
    return property_obj


@router.delete("/properties/{property_id}", status_code=204)
async def delete_property(
    property_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete property (admin only)"""
    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    property_obj = result.scalar_one_or_none()
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    property_obj.is_active = False
    await db.commit()
