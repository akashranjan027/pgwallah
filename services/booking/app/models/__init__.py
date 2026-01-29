"""
Database models for Booking Service
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class PropertyType(str, PyEnum):
    PG = "pg"
    HOSTEL = "hostel"
    APARTMENT = "apartment"


class RoomType(str, PyEnum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    DORMITORY = "dormitory"


class BookingStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Property(Base):
    """PG/Hostel property model"""
    __tablename__ = "properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    property_type = Column(Enum(PropertyType), default=PropertyType.PG)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)  # JSON stringified list
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(255), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to auth user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rooms = relationship("Room", back_populates="property", cascade="all, delete-orphan")


class Room(Base):
    """Room within a property"""
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)
    room_number = Column(String(50), nullable=False)
    room_type = Column(Enum(RoomType), default=RoomType.SINGLE)
    floor = Column(Integer, default=0)
    capacity = Column(Integer, default=1)
    current_occupancy = Column(Integer, default=0)
    rent_amount = Column(Float, nullable=False)
    deposit_amount = Column(Float, default=0)
    is_available = Column(Boolean, default=True)
    amenities = Column(Text, nullable=True)  # JSON stringified list
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property = relationship("Property", back_populates="rooms")
    booking_requests = relationship("BookingRequest", back_populates="room")


class BookingRequest(Base):
    """Booking/membership request from a tenant"""
    __tablename__ = "booking_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to auth tenant
    tenant_name = Column(String(255), nullable=True)
    tenant_email = Column(String(255), nullable=True)
    tenant_phone = Column(String(20), nullable=True)
    move_in_date = Column(DateTime, nullable=False)
    duration_months = Column(Integer, default=1)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    processed_by = Column(UUID(as_uuid=True), nullable=True)  # Admin who processed
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    room = relationship("Room", back_populates="booking_requests")
