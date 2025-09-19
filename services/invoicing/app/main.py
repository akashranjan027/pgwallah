"""
Invoicing Service - Invoices API and Health
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
import logging

logger = logging.getLogger(__name__)

# Try to import invoices router; this may fail if optional deps or DB layer are not ready
try:
    from app.api.invoices import router as invoices_router
    INVOICES_AVAILABLE = True
except Exception as e:
    INVOICES_AVAILABLE = False
    logger.warning("Invoices API not mounted: %s", e)

app = FastAPI(
    title="PGwallah Invoicing Service",
    description="Invoice generation, PDF and email delivery",
    version="1.0.0",
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
# Health at /health (Kong forwards /api/invoices/health -> /health via strip_path)
app.include_router(health_router, prefix="/health", tags=["health"])

# Mount invoices API only if import succeeded
if INVOICES_AVAILABLE:
    app.include_router(invoices_router, prefix="/api/invoices", tags=["invoices"])


@app.get("/")
async def root():
    return {"message": "PGwallah Invoicing Service", "status": "running"}