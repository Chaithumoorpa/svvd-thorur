import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging before anything else
from app.core.logging_config import setup_logging
logger = setup_logging()

# Import settings
from app.core.config import settings

# Import models so Alembic sees them
from app.models import user, temple, pooja, festival, announcement, contact, visitor
from app.api.v1.api import api_router

# Import middleware
from app.core.middleware import (
    RequestLoggingMiddleware,
    SQLTimingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)

# Import debug utilities
if settings.is_development:
    from app.core.debug_utils import log_startup_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    Startup:
    - Validate migrations
    - Log startup info (dev only)
    
    Shutdown:
    - Cleanup resources
    """
    # Startup
    logger.info(f"Starting application in {settings.ENV} mode...")
    
    # Validate migrations
    from app.core.migration_validator import check_migrations_on_startup
    check_migrations_on_startup(
        alembic_config_path=settings.ALEMBIC_CONFIG,
        database_url=settings.DATABASE_URL,
        is_production=settings.is_production
    )
    
    # Log startup info in development
    if settings.is_development:
        log_startup_info()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app with environment-aware settings
app = FastAPI(
    title="Temple Management Backend",
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)

# CORS Configuration (environment-aware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add environment-specific middleware
if settings.is_development:
    # Development middleware
    logger.info("Adding development middleware...")
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SQLTimingMiddleware)
else:
    # Production middleware
    logger.info("Adding production middleware...")
    if settings.ENABLE_SECURITY_HEADERS:
        app.add_middleware(SecurityHeadersMiddleware)
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_PER_MINUTE,
            period=60
        )

# Include API router
app.include_router(api_router)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.ENV,
        "debug": settings.DEBUG,
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Temple Management API",
        "version": "1.0.0",
        "environment": settings.ENV,
        "docs": settings.docs_url or "disabled",
    }
