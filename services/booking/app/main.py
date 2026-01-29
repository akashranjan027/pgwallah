"""
Booking Service - Property and Room Management
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import settings
from app.core.database import create_tables
from app.api.health import router as health_router
from app.api.properties import router as properties_router
from app.api.rooms import router as rooms_router
from app.api.requests import router as requests_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events"""
    # Startup: create tables
    try:
        await create_tables()
        print("Booking DB tables created successfully")
    except Exception as e:
        print(f"Failed to create tables: {e}")
    
    yield
    
    # Shutdown
    print("Booking service shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    description="Property and room booking management service",
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
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(properties_router, tags=["properties"])
app.include_router(rooms_router, tags=["rooms"])
app.include_router(requests_router, tags=["requests"])


@app.get("/")
async def root():
    return {
        "message": "PGwallah Booking Service",
        "status": "running",
        "version": settings.VERSION
    }