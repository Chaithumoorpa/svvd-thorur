import time
from functools import wraps
from fastapi import HTTPException
from typing import Dict, Tuple


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


def get_client_ip(request) -> str:
    """Extract client IP from request."""
    # Check X-Forwarded-For header (proxy)
    if request.headers.get('x-forwarded-for'):
        return request.headers.get('x-forwarded-for').split(',')[0].strip()
    # Fall back to direct connection IP
    return request.client.host


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
