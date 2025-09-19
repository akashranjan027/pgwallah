"""
Health check endpoints for Invoicing service
"""
from datetime import datetime
from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "service": "invoicing-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }