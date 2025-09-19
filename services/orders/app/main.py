"""
PGwallah Orders Service - FastAPI application
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.orders import router as orders_router
from app.core.config import settings
from app.core.database import create_tables

# Optional: simple health router here to avoid extra file
from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orders-service", "version": settings.VERSION}



app = FastAPI(
    title="PGwallah Orders Service",
    description="Food ordering for in-house mess (tenant + kitchen/staff flows)",
    version=settings.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, tags=["health"])
# Alias path to satisfy Kong route /api/orders/health
@app.get("/api/orders/health")
async def health_check_via_api():
    return {"status": "healthy", "service": "orders-service", "version": settings.VERSION}
# Mount at /api/orders so it matches Kong routes (strip_path: false)
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])


@app.on_event("startup")
async def on_startup():
    # Dev convenience: ensure tables exist (use Alembic in production)
    await create_tables()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )