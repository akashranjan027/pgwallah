"""
Mess Menu management endpoints (staff-facing) and public menu APIs.

For development, this uses in-memory storage seeded with a default weekly menu.
In production, replace with DB models and persistence.
"""
import uuid
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

TimeSlot = Literal["breakfast", "lunch", "snacks", "dinner"]
DayOfWeek = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class MenuItem:
    id: str
    name: str
    description: Optional[str]
    price: float
    is_available: bool = True
    slot: TimeSlot = "lunch"


# In-memory store
MENU_ITEMS: Dict[str, MenuItem] = {}
WEEKLY_MENU: Dict[DayOfWeek, Dict[TimeSlot, List[str]]] = {  # maps day -> slot -> list of item IDs
    "monday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
    "tuesday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
    "wednesday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
    "thursday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
    "friday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
    "saturday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
    "sunday": {"breakfast": [], "lunch": [], "snacks": [], "dinner": []},
}


def _add_item(name: str, price: float, slot: TimeSlot, desc: Optional[str] = None) -> str:
    item_id = str(uuid.uuid4())
    MENU_ITEMS[item_id] = MenuItem(
        id=item_id, name=name, description=desc, price=price, slot=slot, is_available=True
    )
    return item_id


def seed_default_weekly_menu() -> None:
    """Seed an Indian mess default weekly menu commonly found in PGs."""
    MENU_ITEMS.clear()
    for d in WEEKLY_MENU.keys():
        WEEKLY_MENU[d]["breakfast"].clear()
        WEEKLY_MENU[d]["lunch"].clear()
        WEEKLY_MENU[d]["snacks"].clear()
        WEEKLY_MENU[d]["dinner"].clear()

    # Breakfast staples
    bf_items = [
        ("Poha", 25.0, "Light flattened rice with peanuts & spices"),
        ("Upma", 25.0, "Semolina porridge with veggies"),
        ("Idli-Sambar", 35.0, "Steamed rice cakes with lentil stew"),
        ("Aloo Paratha + Curd", 40.0, "Stuffed flatbread with potato, served with curd"),
        ("Masala Dosa", 45.0, "Crispy dosa with potato masala"),
        ("Puri-Bhaji", 40.0, "Fried bread with potato curry"),
        ("Bread Omelette", 40.0, "2 eggs omelette with bread"),
    ]
    # Lunch/Dinner staples
    mains = [
        ("Veg Thali", 70.0, "2 sabji, dal, rice, roti, salad"),
        ("Rajma Chawal", 60.0, "Kidney beans in gravy with rice"),
        ("Chole Bhature", 70.0, "Chickpea curry with fried bread"),
        ("Paneer Butter Masala + Roti", 90.0, "Cottage cheese in creamy tomato gravy"),
        ("Mix Veg + Roti", 70.0, "Seasonal vegetables curry"),
        ("Dal Tadka + Jeera Rice", 65.0, "Yellow dal with cumin rice"),
        ("Egg Curry + Rice", 80.0, "Eggs in spicy gravy with rice"),
        ("Chicken Curry + Rice", 120.0, "Non-veg option (if offered)"),
    ]
    # Snacks/Extras
    snacks = [
        ("Samosa (2 pcs)", 25.0, "Fried pastry with spiced potato"),
        ("Pakora Plate", 30.0, "Mixed fritters"),
        ("Tea", 10.0, "Masala chai"),
        ("Coffee", 15.0, "Hot coffee"),
        ("Buttermilk", 15.0, "Chaas"),
    ]

    # Create items
    bf_ids = [_add_item(n, p, "breakfast", d) for n, p, d in bf_items]
    lunch_ids = [_add_item(n, p, "lunch", d) for n, p, d in mains]
    dinner_ids = [_add_item(n, p, "dinner", d) for n, p, d in mains]
    snack_ids = [_add_item(n, p, "snacks", d) for n, p, d in snacks]

    # Assign across days (simple rotation)
    days = list(WEEKLY_MENU.keys())
    for i, day in enumerate(days):
        WEEKLY_MENU[day]["breakfast"] = bf_ids[i % len(bf_ids):] + bf_ids[: i % len(bf_ids)]
        WEEKLY_MENU[day]["lunch"] = lunch_ids[i % len(lunch_ids):] + lunch_ids[: i % len(lunch_ids)]
        WEEKLY_MENU[day]["snacks"] = snack_ids
        WEEKLY_MENU[day]["dinner"] = dinner_ids[(i + 2) % len(dinner_ids):] + dinner_ids[: (i + 2) % len(dinner_ids)]


# Seed on module import (dev only)
seed_default_weekly_menu()


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


@router.get("/menu/items")
async def list_menu_items() -> List[dict]:
    """Return flat list of all menu items."""
    return [asdict(m) for m in MENU_ITEMS.values()]


@router.post("/menu/items", status_code=status.HTTP_201_CREATED)
async def create_menu_item(payload: MenuItemCreate) -> dict:
    """Add a new item to the catalog; staff-facing."""
    item_id = str(uuid.uuid4())
    MENU_ITEMS[item_id] = MenuItem(
        id=item_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        slot=payload.slot,
        is_available=payload.is_available,
    )
    return asdict(MENU_ITEMS[item_id])


@router.put("/menu/items/{item_id}")
async def update_menu_item(item_id: str, payload: MenuItemUpdate) -> dict:
    """Update an existing menu item."""
    item = MENU_ITEMS.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.price is not None:
        item.price = payload.price
    if payload.slot is not None:
        item.slot = payload.slot
    if payload.is_available is not None:
        item.is_available = payload.is_available

    return asdict(item)


@router.delete("/menu/items/{item_id}")
async def delete_menu_item(item_id: str) -> dict:
    """Remove an item from catalog and weekly schedule."""
    if item_id not in MENU_ITEMS:
        raise HTTPException(status_code=404, detail="Menu item not found")
    del MENU_ITEMS[item_id]

    # Remove from weekly mapping
    for day, slots in WEEKLY_MENU.items():
        for slot, ids in slots.items():
            WEEKLY_MENU[day][slot] = [i for i in ids if i != item_id]

    return {"message": "Item deleted"}


class WeeklyMenuResponse(BaseModel):
    weekly: Dict[DayOfWeek, Dict[TimeSlot, List[dict]]]


@router.get("/menu", response_model=WeeklyMenuResponse)
async def get_weekly_menu():
    """Return the weekly menu with item details for each slot."""
    weekly: Dict[str, Dict[str, List[dict]]] = {}
    for day, slots in WEEKLY_MENU.items():
        weekly[day] = {}
        for slot, ids in slots.items():
            weekly[day][slot] = [asdict(MENU_ITEMS[i]) for i in ids if i in MENU_ITEMS]
    return {"weekly": weekly}


class WeeklyAssignPayload(BaseModel):
    day: DayOfWeek
    slot: TimeSlot
    item_ids: List[str] = Field(default_factory=list)


@router.post("/menu/assign")
async def assign_items_to_day_slot(payload: WeeklyAssignPayload) -> dict:
    """Assign a set of item IDs to a day's slot."""
    # validate IDs
    for iid in payload.item_ids:
        if iid not in MENU_ITEMS:
            raise HTTPException(status_code=400, detail=f"Invalid item id {iid}")

    WEEKLY_MENU[payload.day][payload.slot] = payload.item_ids[:]
    return {"message": "Assigned", "day": payload.day, "slot": payload.slot, "count": len(payload.item_ids)}


@router.post("/menu/seed_default")
async def reseed_default() -> dict:
    """Reseed the default weekly menu (dev convenience)."""
    seed_default_weekly_menu()
    return {"message": "Default weekly menu seeded"}