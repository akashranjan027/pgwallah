"""
Mess Menu management endpoints (staff-facing) and public menu APIs.

Uses PostgreSQL for persistence via SQLAlchemy models.
"""
import uuid
from typing import Dict, List, Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import MenuItem as MenuItemModel, WeeklyMenuSlot, TimeSlot as TimeSlotEnum, DayOfWeek as DayOfWeekEnum

router = APIRouter()

TimeSlot = Literal["breakfast", "lunch", "snacks", "dinner"]
DayOfWeek = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


# Pydantic schemas
class MenuItemCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., ge=0)
    slot: TimeSlot = "lunch"
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, ge=0)
    slot: Optional[TimeSlot] = None
    is_available: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: float
    slot: str
    is_available: bool

    class Config:
        from_attributes = True


class WeeklyMenuResponse(BaseModel):
    weekly: Dict[str, Dict[str, List[MenuItemResponse]]]


class WeeklyAssignPayload(BaseModel):
    day: DayOfWeek
    slot: TimeSlot
    item_ids: List[str] = Field(default_factory=list)


def _model_to_dict(item: MenuItemModel) -> dict:
    """Convert SQLAlchemy model to dict for response."""
    return {
        "id": str(item.id),
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "slot": item.slot.value if hasattr(item.slot, 'value') else str(item.slot),
        "is_available": item.is_available,
    }


@router.get("/menu/items")
async def list_menu_items(db: AsyncSession = Depends(get_db)) -> List[dict]:
    """Return flat list of all menu items."""
    result = await db.execute(select(MenuItemModel).order_by(MenuItemModel.name))
    items = result.scalars().all()
    return [_model_to_dict(item) for item in items]


@router.post("/menu/items", status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    payload: MenuItemCreate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Add a new item to the catalog; staff-facing."""
    item = MenuItemModel(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        slot=TimeSlotEnum(payload.slot),
        is_available=payload.is_available,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _model_to_dict(item)


@router.put("/menu/items/{item_id}")
async def update_menu_item(
    item_id: str,
    payload: MenuItemUpdate,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Update an existing menu item."""
    try:
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    result = await db.execute(select(MenuItemModel).where(MenuItemModel.id == item_uuid))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.price is not None:
        item.price = payload.price
    if payload.slot is not None:
        item.slot = TimeSlotEnum(payload.slot)
    if payload.is_available is not None:
        item.is_available = payload.is_available

    await db.commit()
    await db.refresh(item)
    return _model_to_dict(item)


@router.delete("/menu/items/{item_id}")
async def delete_menu_item(
    item_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Remove an item from catalog and weekly schedule."""
    try:
        item_uuid = UUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    
    result = await db.execute(select(MenuItemModel).where(MenuItemModel.id == item_uuid))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Remove from weekly schedule first
    await db.execute(delete(WeeklyMenuSlot).where(WeeklyMenuSlot.menu_item_id == item_uuid))
    
    # Delete the item
    await db.delete(item)
    await db.commit()

    return {"message": "Item deleted"}


@router.get("/menu", response_model=WeeklyMenuResponse)
async def get_weekly_menu(db: AsyncSession = Depends(get_db)):
    """Return the weekly menu with item details for each slot."""
    # Initialize empty structure
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    slots = ["breakfast", "lunch", "snacks", "dinner"]
    
    weekly: Dict[str, Dict[str, List[dict]]] = {
        day: {slot: [] for slot in slots} for day in days
    }
    
    # Fetch all weekly menu slots with their items
    result = await db.execute(
        select(WeeklyMenuSlot)
        .order_by(WeeklyMenuSlot.day, WeeklyMenuSlot.slot, WeeklyMenuSlot.display_order)
    )
    menu_slots = result.scalars().all()
    
    for slot_entry in menu_slots:
        day_key = slot_entry.day.value if hasattr(slot_entry.day, 'value') else str(slot_entry.day)
        slot_key = slot_entry.slot.value if hasattr(slot_entry.slot, 'value') else str(slot_entry.slot)
        if slot_entry.menu_item:
            weekly[day_key][slot_key].append(_model_to_dict(slot_entry.menu_item))
    
    return {"weekly": weekly}


@router.post("/menu/assign")
async def assign_items_to_day_slot(
    payload: WeeklyAssignPayload,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Assign a set of item IDs to a day's slot."""
    day_enum = DayOfWeekEnum(payload.day)
    slot_enum = TimeSlotEnum(payload.slot)
    
    # Validate all item IDs exist
    for iid in payload.item_ids:
        try:
            item_uuid = UUID(iid)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid item id format: {iid}")
        
        result = await db.execute(select(MenuItemModel).where(MenuItemModel.id == item_uuid))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Invalid item id {iid}")

    # Remove existing assignments for this day/slot
    await db.execute(
        delete(WeeklyMenuSlot).where(
            WeeklyMenuSlot.day == day_enum,
            WeeklyMenuSlot.slot == slot_enum
        )
    )

    # Create new assignments
    for order, iid in enumerate(payload.item_ids):
        slot_entry = WeeklyMenuSlot(
            day=day_enum,
            slot=slot_enum,
            menu_item_id=UUID(iid),
            display_order=order
        )
        db.add(slot_entry)
    
    await db.commit()
    return {"message": "Assigned", "day": payload.day, "slot": payload.slot, "count": len(payload.item_ids)}


@router.post("/menu/seed_default")
async def reseed_default(db: AsyncSession = Depends(get_db)) -> dict:
    """Seed the default weekly menu into the database."""
    # Clear existing data
    await db.execute(delete(WeeklyMenuSlot))
    await db.execute(delete(MenuItemModel))
    await db.commit()
    
    # Breakfast staples
    bf_items = [
        ("Poha", 25.0, "breakfast", "Light flattened rice with peanuts & spices"),
        ("Upma", 25.0, "breakfast", "Semolina porridge with veggies"),
        ("Idli-Sambar", 35.0, "breakfast", "Steamed rice cakes with lentil stew"),
        ("Aloo Paratha + Curd", 40.0, "breakfast", "Stuffed flatbread with potato, served with curd"),
        ("Masala Dosa", 45.0, "breakfast", "Crispy dosa with potato masala"),
        ("Puri-Bhaji", 40.0, "breakfast", "Fried bread with potato curry"),
        ("Bread Omelette", 40.0, "breakfast", "2 eggs omelette with bread"),
    ]
    
    # Lunch staples
    lunch_items = [
        ("Veg Thali", 70.0, "lunch", "2 sabji, dal, rice, roti, salad"),
        ("Rajma Chawal", 60.0, "lunch", "Kidney beans in gravy with rice"),
        ("Chole Bhature", 70.0, "lunch", "Chickpea curry with fried bread"),
        ("Paneer Butter Masala + Roti", 90.0, "lunch", "Cottage cheese in creamy tomato gravy"),
        ("Mix Veg + Roti", 70.0, "lunch", "Seasonal vegetables curry"),
        ("Dal Tadka + Jeera Rice", 65.0, "lunch", "Yellow dal with cumin rice"),
        ("Egg Curry + Rice", 80.0, "lunch", "Eggs in spicy gravy with rice"),
        ("Chicken Curry + Rice", 120.0, "lunch", "Non-veg option (if offered)"),
    ]
    
    # Dinner staples
    dinner_items = [
        ("Veg Thali", 70.0, "dinner", "2 sabji, dal, rice, roti, salad"),
        ("Rajma Chawal", 60.0, "dinner", "Kidney beans in gravy with rice"),
        ("Chole Bhature", 70.0, "dinner", "Chickpea curry with fried bread"),
        ("Paneer Butter Masala + Roti", 90.0, "dinner", "Cottage cheese in creamy tomato gravy"),
        ("Mix Veg + Roti", 70.0, "dinner", "Seasonal vegetables curry"),
        ("Dal Tadka + Jeera Rice", 65.0, "dinner", "Yellow dal with cumin rice"),
        ("Egg Curry + Rice", 80.0, "dinner", "Eggs in spicy gravy with rice"),
        ("Chicken Curry + Rice", 120.0, "dinner", "Non-veg option (if offered)"),
    ]
    
    # Snacks
    snack_items = [
        ("Samosa (2 pcs)", 25.0, "snacks", "Fried pastry with spiced potato"),
        ("Pakora Plate", 30.0, "snacks", "Mixed fritters"),
        ("Tea", 10.0, "snacks", "Masala chai"),
        ("Coffee", 15.0, "snacks", "Hot coffee"),
        ("Buttermilk", 15.0, "snacks", "Chaas"),
    ]
    
    all_items = bf_items + lunch_items + dinner_items + snack_items
    created_items: Dict[str, Dict[str, MenuItemModel]] = {
        "breakfast": {},
        "lunch": {},
        "dinner": {},
        "snacks": {},
    }
    
    # Create menu items
    for name, price, slot, desc in all_items:
        item = MenuItemModel(
            name=name,
            description=desc,
            price=price,
            slot=TimeSlotEnum(slot),
            is_available=True
        )
        db.add(item)
        await db.flush()
        created_items[slot][name] = item
    
    # Assign to weekly schedule - simple rotation
    days = list(DayOfWeekEnum)
    slots_map = {
        "breakfast": list(created_items["breakfast"].values()),
        "lunch": list(created_items["lunch"].values()),
        "dinner": list(created_items["dinner"].values()),
        "snacks": list(created_items["snacks"].values()),
    }
    
    for i, day in enumerate(days):
        # Breakfast - rotate items
        bf_list = slots_map["breakfast"]
        rotated_bf = bf_list[i % len(bf_list):] + bf_list[:i % len(bf_list)]
        for order, item in enumerate(rotated_bf):
            db.add(WeeklyMenuSlot(day=day, slot=TimeSlotEnum.BREAKFAST, menu_item_id=item.id, display_order=order))
        
        # Lunch - rotate items
        lunch_list = slots_map["lunch"]
        rotated_lunch = lunch_list[i % len(lunch_list):] + lunch_list[:i % len(lunch_list)]
        for order, item in enumerate(rotated_lunch):
            db.add(WeeklyMenuSlot(day=day, slot=TimeSlotEnum.LUNCH, menu_item_id=item.id, display_order=order))
        
        # Dinner - rotate with offset
        dinner_list = slots_map["dinner"]
        rotated_dinner = dinner_list[(i+2) % len(dinner_list):] + dinner_list[:(i+2) % len(dinner_list)]
        for order, item in enumerate(rotated_dinner):
            db.add(WeeklyMenuSlot(day=day, slot=TimeSlotEnum.DINNER, menu_item_id=item.id, display_order=order))
        
        # Snacks - same for all days
        for order, item in enumerate(slots_map["snacks"]):
            db.add(WeeklyMenuSlot(day=day, slot=TimeSlotEnum.SNACKS, menu_item_id=item.id, display_order=order))
    
    await db.commit()
    return {"message": "Default weekly menu seeded to database"}