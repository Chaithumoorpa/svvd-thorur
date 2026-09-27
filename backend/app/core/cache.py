"""Process-local TTL cache for read-heavy public endpoints (temple profile,
timings, poojas, festivals, announcements, gallery) - cuts repeat database
hits for content that rarely changes, without adding new infrastructure
(no Redis) at a scale where one small EC2 instance is the whole deployment.

Not shared across processes: production runs the backend with multiple
uvicorn workers (see docker-compose.prod.yml), each with its own cache and
its own copy of every key. `invalidate()` only clears the calling worker's
copy, so an edit is guaranteed fresh on whichever worker served the write,
but another worker may still serve a stale read for up to `ttl` more
seconds - the same trade-off SimpleRateLimiter already makes for rate
limits, and an acceptable one here since nothing cached is security-
sensitive and the TTL is short."""
import threading
from typing import Callable, TypeVar

from cachetools import TTLCache

T = TypeVar("T")

_ttl_seconds = 45
_cache: TTLCache = TTLCache(maxsize=512, ttl=_ttl_seconds)
_lock = threading.Lock()
_MISSING = object()


def cached(key: str, compute: Callable[[], T]) -> T:
    with _lock:
        value = _cache.get(key, _MISSING)
    if value is not _MISSING:
        return value  # type: ignore[return-value]
    value = compute()
    with _lock:
        _cache[key] = value
    return value


def invalidate(prefix: str) -> None:
    """Drop every cached key starting with `prefix` on this worker, so a
    write is visible immediately to requests this same worker serves next."""
    with _lock:
        for key in [k for k in _cache if k.startswith(prefix)]:
            del _cache[key]
