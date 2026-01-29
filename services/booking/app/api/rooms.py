"""
Rooms API endpoints
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Room, Property
from app.schemas import (
    RoomCreate, RoomUpdate, RoomResponse, RoomListResponse
)

router = APIRouter()


@router.get("/rooms", response_model=RoomListResponse)
async def list_rooms(
    property_id: Optional[UUID] = None,
    room_type: Optional[str] = None,
    is_available: Optional[bool] = None,
    min_rent: Optional[float] = None,
    max_rent: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List rooms with optional filters"""
    query = select(Room)
    
    if property_id:
        query = query.where(Room.property_id == property_id)
    if room_type:
        query = query.where(Room.room_type == room_type)
    if is_available is not None:
        query = query.where(Room.is_available == is_available)
    if min_rent:
        query = query.where(Room.rent_amount >= min_rent)
    if max_rent:
        query = query.where(Room.rent_amount <= max_rent)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get items
    query = query.offset(skip).limit(limit).order_by(Room.rent_amount)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return RoomListResponse(items=items, total=total or 0)


@router.post("/rooms", response_model=RoomResponse, status_code=201)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new room (admin only)"""
    # Verify property exists
    result = await db.execute(
        select(Property).where(Property.id == data.property_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Property not found")
    
    room = Room(
        property_id=data.property_id,
        room_number=data.room_number,
        room_type=data.room_type,
        floor=data.floor,
        capacity=data.capacity,
        rent_amount=data.rent_amount,
        deposit_amount=data.deposit_amount,
        amenities=data.amenities,
    )
    
    db.add(room)
    await db.commit()
    await db.refresh(room)
    
    return room


@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get room by ID"""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return room


@router.get("/availability", response_model=RoomListResponse)
async def check_availability(
    property_id: Optional[UUID] = None,
    room_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get available rooms"""
    query = select(Room).where(
        Room.is_available == True,
        Room.current_occupancy < Room.capacity
    )
    
    if property_id:
        query = query.where(Room.property_id == property_id)
    if room_type:
        query = query.where(Room.room_type == room_type)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get items
    query = query.offset(skip).limit(limit).order_by(Room.rent_amount)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return RoomListResponse(items=items, total=total or 0)


@router.put("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update room (admin only)"""
    result = await db.execute(
        select(Room).where(Room.id == room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(room, field, value)
    
    await db.commit()
    await db.refresh(room)
    
    return room
