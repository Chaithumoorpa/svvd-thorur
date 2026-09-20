import time
from functools import wraps
from fastapi import HTTPException
from typing import Dict, Tuple

from app.core.config import settings


class SimpleRateLimiter:
    """
    Simple in-memory rate limiter.
    Tracks requests per IP address.
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if client is within rate limit."""
        now = time.time()
        
        # Initialize if first request from this IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[client_ip].append(now)
        return True


# Rate limiters for auth endpoints
# 5 requests per minute per IP
login_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60)
register_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60)
# Public write endpoints: 5 contact messages / 10 seva bookings per IP per hour
contact_limiter = SimpleRateLimiter(max_requests=5, window_seconds=3600)
booking_limiter = SimpleRateLimiter(max_requests=10, window_seconds=3600)


def get_client_ip(request) -> str:
    """
    Client IP for rate limiting / visitor hashing.

    X-Forwarded-For is client-controlled unless a trusted proxy overwrites it,
    so it is only honoured when TRUST_PROXY_HEADERS is enabled.
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            hops = [h.strip() for h in forwarded.split(",") if h.strip()]
            if hops:
                # each trusted proxy appends the address it saw; count from the right
                return hops[-min(settings.TRUSTED_PROXY_HOPS, len(hops))]
    return request.client.host if request.client else "unknown"


def rate_limit_login(limiter: SimpleRateLimiter):
    """Decorator to rate limit login endpoint."""
    def decorator(func):
        @wraps(func)
        def wrapper(payload, service, request):
            client_ip = get_client_ip(request)
            if not limiter.is_allowed(client_ip):
                raise HTTPException(
                    status_code=429,
                    detail="Too many login attempts. Please try again in a minute."
                )
            return func(payload, service, request)
        return wrapper
    return decorator
