import time
import threading
from typing import Dict, List, Optional

from fastapi import HTTPException, Request

from app.core.config import settings


class SimpleRateLimiter:
    """
    Sliding-window, in-memory rate limiter keyed by an arbitrary string
    (client IP, username, ...).

    - Thread-safe: FastAPI runs sync endpoints in a thread pool.
    - Bounded memory: keys whose window has expired are dropped, so a flood of
      distinct keys cannot grow the dict forever.
    - State is per process. Run a single uvicorn worker (or move to Redis) if
      you need one global limit.
    """

    _SWEEP_EVERY = 500  # full sweep of stale keys every N calls

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._calls = 0

    def _sweep(self, now: float) -> None:
        cutoff = now - self.window_seconds
        stale = [k for k, ts in self.requests.items() if not ts or ts[-1] <= cutoff]
        for k in stale:
            del self.requests[k]

    def is_allowed(self, key: str) -> bool:
        """Return True and record the hit if `key` is within its limit."""
        now = time.time()
        cutoff = now - self.window_seconds
        with self._lock:
            self._calls += 1
            if self._calls % self._SWEEP_EVERY == 0:
                self._sweep(now)

            recent = [t for t in self.requests.get(key, []) if t > cutoff]
            if len(recent) >= self.max_requests:
                self.requests[key] = recent
                return False

            recent.append(now)
            self.requests[key] = recent
            return True


# --- Limiters -------------------------------------------------------------
# Auth endpoints: 5 attempts per minute per client IP.
login_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60)
register_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60)
# Per-account brake so distributed guessing against one username still slows down.
login_user_limiter = SimpleRateLimiter(max_requests=10, window_seconds=15 * 60)
# Public write endpoints that could otherwise be used to flood the database
# (and, once admin email alerts exist, the admin's inbox).
contact_limiter = SimpleRateLimiter(max_requests=5, window_seconds=60 * 60)
booking_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60 * 60)
visit_limiter = SimpleRateLimiter(max_requests=30, window_seconds=60)
payment_order_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60 * 60)


def get_client_ip(request: Request, trusted_hops: Optional[int] = None) -> str:
    """
    Best-effort real client IP that a client cannot spoof.

    X-Forwarded-For looks like "client-supplied, ..., address-seen-by-proxy-1".
    Each trusted proxy appends the address it received the request from, so with
    N trusted proxies the real client is the N-th entry counted from the RIGHT.
    Entries further left are whatever the client chose to send.

    With TRUSTED_PROXY_HOPS=0 (default) the header is ignored entirely.
    """
    hops = settings.TRUSTED_PROXY_HOPS if trusted_hops is None else trusted_hops
    peer = request.client.host if request.client else "unknown"
    if hops <= 0:
        return peer

    header = request.headers.get("x-forwarded-for", "")
    parts = [p.strip() for p in header.split(",") if p.strip()]
    if len(parts) < hops:
        # Fewer entries than expected proxies: header is missing or the request
        # bypassed the proxy. Do not guess - use the socket peer.
        return peer
    return parts[-hops]


def enforce(limiter: SimpleRateLimiter, key: str, message: str) -> None:
    """Raise HTTP 429 when `key` has exceeded `limiter`."""
    if not limiter.is_allowed(key):
        raise HTTPException(
            status_code=429,
            detail=message,
            headers={"Retry-After": str(limiter.window_seconds)},
        )
