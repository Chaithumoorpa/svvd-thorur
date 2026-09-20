"""
Middleware for development debugging and production security.
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.rate_limiter import get_client_ip

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all incoming requests and responses (DEVELOPMENT ONLY).
    
    Logs:
    - Request method, path, query params
    - Request headers
    - Response status code
    - Response time
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.debug(f"→ {request.method} {request.url.path}")
        logger.debug(f"  Query params: {dict(request.query_params)}")
        safe_headers = {
            k: ("<redacted>" if k.lower() in {"authorization", "cookie"} else v)
            for k, v in request.headers.items()
        }
        logger.debug(f"  Headers: {safe_headers}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response
        logger.debug(f"← {response.status_code} {request.url.path} ({process_time:.3f}s)")
        
        # Add response time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class SQLTimingMiddleware(BaseHTTPMiddleware):
    """
    Log SQL query timing information (DEVELOPMENT ONLY).
    
    Note: Actual SQL logging is handled by SQLAlchemy echo=True,
    this middleware just adds timing context.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Log if request took significant time
        if total_time > 0.5:  # More than 500ms
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {total_time:.3f}s"
            )
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses (PRODUCTION ONLY).
    
    Headers:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Content-Security-Policy
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # HSTS - Force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting (PRODUCTION ONLY).
    
    Note: For production, consider using Redis-based rate limiting
    for distributed systems.
    """
    
    def __init__(self, app: ASGIApp, calls: int = 60, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = get_client_ip(request)
        
        # Get current time
        current_time = time.time()
        
        # Clean old entries
        self.clients = {
            ip: timestamps
            for ip, timestamps in self.clients.items()
            if any(t > current_time - self.period for t in timestamps)
        }
        
        # Get client's request history
        if client_ip not in self.clients:
            self.clients[client_ip] = []
        
        # Filter recent requests
        recent_requests = [
            t for t in self.clients[client_ip]
            if t > current_time - self.period
        ]
        
        # Check rate limit
        if len(recent_requests) >= self.calls:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Add current request
        recent_requests.append(current_time)
        self.clients[client_ip] = recent_requests
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(
            self.calls - len(recent_requests)
        )
        
        return response
