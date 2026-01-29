"""
Pydantic schemas for Booking Service
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# Enums
class PropertyType(str):
    PG = "pg"
    HOSTEL = "hostel"
    APARTMENT = "apartment"


class RoomType(str):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    DORMITORY = "dormitory"


class BookingStatus(str):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# Property Schemas
class PropertyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., min_length=5, max_length=10)
    property_type: str = "pg"
    description: Optional[str] = None
    amenities: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class PropertyCreate(PropertyBase):
    owner_id: Optional[UUID] = None


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None


class PropertyResponse(PropertyBase):
    id: UUID
    owner_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Room Schemas
class RoomBase(BaseModel):
    room_number: str = Field(..., max_length=50)
    room_type: str = "single"
    floor: int = 0
    capacity: int = 1
    rent_amount: float = Field(..., gt=0)
    deposit_amount: float = 0
    amenities: Optional[str] = None


class RoomCreate(RoomBase):
    property_id: UUID


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    floor: Optional[int] = None
    capacity: Optional[int] = None
    rent_amount: Optional[float] = None
    deposit_amount: Optional[float] = None
    is_available: Optional[bool] = None
    current_occupancy: Optional[int] = None
    amenities: Optional[str] = None


class RoomResponse(RoomBase):
    id: UUID
    property_id: UUID
    current_occupancy: int
    is_available: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Booking Request Schemas
class BookingRequestCreate(BaseModel):
    room_id: UUID
    tenant_id: UUID
    tenant_name: Optional[str] = None
    tenant_email: Optional[str] = None
    tenant_phone: Optional[str] = None
    move_in_date: datetime
    duration_months: int = Field(1, ge=1)
    notes: Optional[str] = None


class BookingRequestUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None
    processed_by: Optional[UUID] = None


class BookingRequestResponse(BaseModel):
    id: UUID
    room_id: UUID
    tenant_id: UUID
    tenant_name: Optional[str] = None
    tenant_email: Optional[str] = None
    tenant_phone: Optional[str] = None
    move_in_date: datetime
    duration_months: int
    status: str
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    processed_by: Optional[UUID] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# List responses
class PropertyListResponse(BaseModel):
    items: List[PropertyResponse]
    total: int


class RoomListResponse(BaseModel):
    items: List[RoomResponse]
    total: int


class BookingRequestListResponse(BaseModel):
    items: List[BookingRequestResponse]
    total: int
