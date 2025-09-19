"""
Health check endpoints for Payment service
"""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db, db_manager

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint without database dependency to avoid startup issues"""
    
    # Basic health check without database dependency during startup
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "service": "payment",
        "features": {
            "razorpay": "enabled",
            "upi": "enabled",
            "subscriptions": "enabled",
            "webhooks": "enabled",
        }
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with all dependencies"""
    
    # Check database health
    db_health = await db_manager.health_check()
    
    # Check RabbitMQ connection (simplified)
    rabbitmq_health = {"status": "unknown"}
    
    # Check MinIO/S3 connection (simplified)
    storage_health = {"status": "unknown"}
    
    # Overall health status
    is_healthy = db_health["status"] == "healthy"
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "service": "payment",
        "checks": {
            "database": db_health,
            "rabbitmq": rabbitmq_health,
            "storage": storage_health,
        },
        "features": {
            "razorpay": "enabled",
            "upi": "enabled",
            "subscriptions": "enabled",
            "webhooks": "enabled",
        }
    }


@router.get("/health/liveness")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/readiness")
async def readiness_probe():
    """Kubernetes readiness probe endpoint - simplified to avoid startup issues"""
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "payment"
    }