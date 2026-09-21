import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

# Configure logging before anything else
from app.core.logging_config import setup_logging
logger = setup_logging()

# Import settings
from app.core.config import settings

# Import models so Alembic sees them
import app.models  # noqa: F401  (registers every model with SQLAlchemy metadata)
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
    version="2.0.0",
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
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
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
    if settings.security_headers_enabled:
        app.add_middleware(SecurityHeadersMiddleware)
    if settings.rate_limiting_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_PER_MINUTE,
            period=60
        )

# Include API router
app.include_router(api_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Starlette's own default 500 handler returns this exact plain-text body
    # but doesn't reliably surface a traceback in this deployment's logs
    # (uvicorn's --log-level flag interacts oddly with our own logging
    # config) - log explicitly through our configured logger so a real bug
    # doesn't look identical to "nothing happened" in `docker compose logs`.
    logger.error(f"Unhandled exception on {request.method} {request.url.path}", exc_info=exc)
    return PlainTextResponse("Internal Server Error", status_code=500)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Temple Management API",
        "version": "2.0.0",
        "docs": settings.docs_url or "disabled",
    }
