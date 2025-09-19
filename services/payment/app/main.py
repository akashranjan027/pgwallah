"""
Main FastAPI application for Payment service
"""
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.api import health, payments
from app.core.config import settings
from app.core.database import db_manager, create_tables
from app.utils.events import event_publisher

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "payment_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "payment_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)

PAYMENT_COUNT = Counter(
    "payments_total",
    "Total number of payments",
    ["status", "method", "purpose"]
)

PAYMENT_AMOUNT = Histogram(
    "payment_amount_rupees",
    "Payment amounts in rupees",
    ["purpose"]
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Payment service", version=settings.VERSION, environment=settings.ENVIRONMENT)

    # Dev convenience: ensure tables exist (use Alembic in production)
    try:
        await create_tables()
        logger.info("Payment DB tables ensured")
    except Exception as e:
        logger.warning("Failed to ensure payment tables", error=str(e))

    # Connect to RabbitMQ for event publishing
    try:
        await event_publisher.connect()
        logger.info("Connected to RabbitMQ for event publishing")
    except Exception as e:
        logger.warning("Failed to connect to RabbitMQ", error=str(e))
    
    logger.info("Payment service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Payment service")
    await event_publisher.disconnect()
    await db_manager.close()
    logger.info("Payment service shut down complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Payment and billing service with Razorpay UPI integration",
    openapi_url="/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time and logging"""
    start_time = time.time()
    
    # Add correlation ID if not present
    correlation_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        correlation_id=correlation_id,
        user_agent=request.headers.get("User-Agent"),
        client_ip=request.client.host if request.client else None,
    )
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Add headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = correlation_id
    
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
        correlation_id=correlation_id,
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    correlation_id = request.headers.get("X-Request-ID", "unknown")
    
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        method=request.method,
        path=request.url.path,
        correlation_id=correlation_id,
        exc_info=True,
    )
    
    if settings.DEBUG:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc),
                "correlation_id": correlation_id,
                "traceback": traceback.format_exc().split('\n') if settings.DEBUG else None,
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
        }
    )


# Prometheus metrics endpoint
@app.get("/metrics", response_class=Response)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include routers
app.include_router(health.router, prefix="", tags=["Health"])
app.include_router(payments.router, prefix="", tags=["Payments"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "razorpay_integration": "enabled",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )