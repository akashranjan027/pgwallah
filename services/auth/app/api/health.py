"""
Health check endpoints
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, db_manager

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint
    Returns the overall health status of the service
    """
    # Check database health
    db_health = await db_manager.health_check()
    
    # Overall health status
    is_healthy = db_health["status"] == "healthy"
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "service": "auth",
        "checks": {
            "database": db_health,
        }
    }


@router.get("/health/liveness")
async def liveness_probe():
    """
    Kubernetes liveness probe endpoint
    Returns 200 if the service is alive
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/readiness")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint
    Returns 200 if the service is ready to serve traffic
    """
    # Check if database is accessible
    db_health = await db_manager.health_check()
    
    if db_health["status"] != "healthy":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Service not ready - database connection failed"
        )
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "healthy"
        }
    }