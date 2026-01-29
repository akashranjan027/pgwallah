"""
Booking Requests API endpoints
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import BookingRequest, Room, BookingStatus
from app.schemas import (
    BookingRequestCreate, BookingRequestUpdate, 
    BookingRequestResponse, BookingRequestListResponse
)

router = APIRouter()


@router.get("/requests", response_model=BookingRequestListResponse)
async def list_requests(
    tenant_id: Optional[UUID] = None,
    room_id: Optional[UUID] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List booking requests with optional filters"""
    query = select(BookingRequest)
    
    if tenant_id:
        query = query.where(BookingRequest.tenant_id == tenant_id)
    if room_id:
        query = query.where(BookingRequest.room_id == room_id)
    if status:
        query = query.where(BookingRequest.status == status)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get items
    query = query.offset(skip).limit(limit).order_by(BookingRequest.created_at.desc())
    result = await db.execute(query)
    items = result.scalars().all()
    
    return BookingRequestListResponse(items=items, total=total or 0)


@router.post("/requests", response_model=BookingRequestResponse, status_code=201)
async def create_request(
    data: BookingRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new booking request"""
    # Verify room exists and is available
    result = await db.execute(
        select(Room).where(Room.id == data.room_id)
    )
    room = result.scalar_one_or_none()
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if not room.is_available:
        raise HTTPException(status_code=400, detail="Room is not available")
    
    if room.current_occupancy >= room.capacity:
        raise HTTPException(status_code=400, detail="Room is at full capacity")
    
    booking = BookingRequest(
        room_id=data.room_id,
        tenant_id=data.tenant_id,
        tenant_name=data.tenant_name,
        tenant_email=data.tenant_email,
        tenant_phone=data.tenant_phone,
        move_in_date=data.move_in_date,
        duration_months=data.duration_months,
        notes=data.notes,
    )
    
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    
    return booking


@router.get("/requests/{request_id}", response_model=BookingRequestResponse)
async def get_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get booking request by ID"""
    result = await db.execute(
        select(BookingRequest).where(BookingRequest.id == request_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")
    
    return booking


@router.put("/requests/{request_id}", response_model=BookingRequestResponse)
async def update_request(
    request_id: UUID,
    data: BookingRequestUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update booking request status (admin only)"""
    result = await db.execute(
        select(BookingRequest).where(BookingRequest.id == request_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        update_data["processed_at"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(booking, field, value)
    
    # If confirmed, update room occupancy
    if data.status == BookingStatus.CONFIRMED:
        room_result = await db.execute(
            select(Room).where(Room.id == booking.room_id)
        )
        room = room_result.scalar_one_or_none()
        if room:
            room.current_occupancy += 1
            if room.current_occupancy >= room.capacity:
                room.is_available = False
    
    await db.commit()
    await db.refresh(booking)
    
    return booking


@router.post("/requests/{request_id}/confirm", response_model=BookingRequestResponse)
async def confirm_request(
    request_id: UUID,
    admin_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """Confirm a booking request (admin only)"""
    result = await db.execute(
        select(BookingRequest).where(BookingRequest.id == request_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")
    
    if booking.status != BookingStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot confirm request in {booking.status} status"
        )
    
    # Update booking status
    booking.status = BookingStatus.CONFIRMED
    booking.processed_by = admin_id
    booking.processed_at = datetime.utcnow()
    
    # Update room occupancy
    room_result = await db.execute(
        select(Room).where(Room.id == booking.room_id)
    )
    room = room_result.scalar_one_or_none()
    if room:
        room.current_occupancy += 1
        if room.current_occupancy >= room.capacity:
            room.is_available = False
    
    await db.commit()
    await db.refresh(booking)
    
    return booking


@router.delete("/requests/{request_id}", status_code=204)
async def cancel_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a booking request"""
    result = await db.execute(
        select(BookingRequest).where(BookingRequest.id == request_id)
    )
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking request not found")
    
    booking.status = BookingStatus.CANCELLED
    await db.commit()
