"""
Helpers to fetch Mess menu items for validation/pricing in Orders service.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


async def get_menu_items_from_mess_service() -> List[Dict[str, Any]]:
    """
    Fetch flat menu item catalog from Mess service.

    Returns a list of items:
      [
        {
          "id": "uuid",
          "name": "Poha",
          "description": "...",
          "price": 25.0,
          "is_available": true,
          "slot": "breakfast"
        },
        ...
      ]
    """
    base_url = settings.MESS_SERVICE_URL or os.getenv("MESS_SERVICE_URL") or "http://mess:8050"
    url = f"{base_url}/api/mess/menu/items"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                logger.warning("unexpected_menu_items_payload", payload_type=type(data))
                return []
            # Basic normalization and filtering
            normalized: List[Dict[str, Any]] = []
            for item in data:
                try:
                    normalized.append(
                        {
                            "id": str(item.get("id")),
                            "name": str(item.get("name")),
                            "description": item.get("description"),
                            "price": float(item.get("price", 0.0)),
                            "is_available": bool(item.get("is_available", True)),
                            "slot": item.get("slot") or "lunch",
                        }
                    )
                except Exception as e:
                    logger.warning("menu_item_normalization_failed", error=str(e), item=item)
            return normalized
    except Exception as e:
        logger.error("fetch_menu_items_failed", error=str(e), url=url)
        # Fail closed: return empty list so caller can raise 400 if needed
        return []