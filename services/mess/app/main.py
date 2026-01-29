"""
Mess Service - Dining and Attendance Management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.menu import router as menu_router
from app.api.coupons import router as coupons_router
from app.core.config import settings

app = FastAPI(
    title="PGwallah Mess Service",
    description="Dining and attendance management service",
    version=settings.VERSION,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])
# Mount staff/public menu under /api/mess to align with Kong routes
app.include_router(menu_router, prefix="/api/mess", tags=["menu"])
# Coupons endpoints (issue/redeem/list)
app.include_router(coupons_router, prefix="/api/mess", tags=["coupons"])


@app.get("/")
async def root():
    return {"message": "PGwallah Mess Service", "status": "running", "version": settings.VERSION}