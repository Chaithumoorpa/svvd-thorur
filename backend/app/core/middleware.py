"""
Middleware for development debugging and production security.
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

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
        logger.debug(f"  Headers: {dict(request.headers)}")
        
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
    Site-wide per-client rate limit (PRODUCTION ONLY).

    Clients are identified with get_client_ip(), which honours
    TRUSTED_PROXY_HOPS. Previously this keyed on the TCP peer, which behind
    Nginx/Docker is the proxy itself, so *all* visitors shared one bucket and a
    few dozen users on a festival day would start receiving 429s.

    State is per process; for a single global limit run one uvicorn worker.
    """

    EXEMPT_PATHS = {"/health"}

    def __init__(self, app: ASGIApp, calls: int = 60, period: int = 60):
        super().__init__(app)
        # Imported here to avoid a circular import at module load time.
        from app.utils.rate_limiter import SimpleRateLimiter, get_client_ip

        self.calls = calls
        self.period = period
        self._limiter = SimpleRateLimiter(max_requests=calls, window_seconds=period)
        self._get_client_ip = get_client_ip

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if not self._limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={
                    "Retry-After": str(self.period),
                    "X-RateLimit-Limit": str(self.calls),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        return response
