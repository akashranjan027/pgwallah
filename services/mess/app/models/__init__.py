"""
Database models for Mess Service
"""
import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TimeSlot(str, PyEnum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACKS = "snacks"
    DINNER = "dinner"


class DayOfWeek(str, PyEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class MenuItem(Base):
    """Menu item catalog"""
    __tablename__ = "menu_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    slot = Column(Enum(TimeSlot), default=TimeSlot.LUNCH)
    is_available = Column(Boolean, default=True)
    category = Column(String(100), nullable=True)  # e.g., "veg", "non-veg", "snacks"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WeeklyMenuSlot(Base):
    """Mapping of menu items to weekly schedule"""
    __tablename__ = "weekly_menu_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    day = Column(Enum(DayOfWeek), nullable=False)
    slot = Column(Enum(TimeSlot), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    display_order = Column(Integer, default=0)
    
    # Relationship
    menu_item = relationship("MenuItem")


class MealCoupon(Base):
    """Meal coupons issued to tenants"""
    __tablename__ = "meal_coupons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to auth tenant
    for_date = Column(Date, nullable=False)
    slot = Column(Enum(TimeSlot), nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MealAttendance(Base):
    """Track meal attendance for tenants"""
    __tablename__ = "meal_attendance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    for_date = Column(Date, nullable=False)
    slot = Column(Enum(TimeSlot), nullable=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    marked_by = Column(UUID(as_uuid=True), nullable=True)  # Staff who marked
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("meal_coupons.id"), nullable=True)
    
    # Relationship
    coupon = relationship("MealCoupon")
