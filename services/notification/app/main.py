"""
Notification Service - Email and SMS Notifications
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import settings
from app.core.database import create_tables
from app.api.notifications import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events"""
    # Startup: create tables
    try:
        await create_tables()
        print("Notification DB tables created successfully")
    except Exception as e:
        print(f"Failed to create tables: {e}")
    
    yield
    
    # Shutdown
    print("Notification service shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="Email and SMS notification service",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(notifications_router, prefix="", tags=["notifications"])


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": settings.VERSION
    }


@app.get("/")
async def root():
    return {
        "message": "PGwallah Notification Service",
        "status": "running",
        "version": settings.VERSION
    }
