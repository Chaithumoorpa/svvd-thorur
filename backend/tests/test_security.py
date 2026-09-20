"""Security regression tests found in code review."""
import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import Settings
from app.utils.rate_limiter import SimpleRateLimiter, get_client_ip


def make_request(peer="10.0.0.5", xff=None) -> Request:
    headers = [(b"x-forwarded-for", xff.encode())] if xff is not None else []
    scope = {"type": "http", "headers": headers, "client": (peer, 1234), "method": "GET", "path": "/"}
    return Request(scope)


# --- client IP / X-Forwarded-For ------------------------------------------------

def test_xff_ignored_by_default():
    # 0 trusted proxies: a client-supplied header must not change identity.
    assert get_client_ip(make_request(peer="10.0.0.5", xff="1.2.3.4")) == "10.0.0.5"


def test_spoofed_leftmost_entry_is_ignored_with_one_proxy():
    # Nginx/Caddy appends the real peer on the right; the left is attacker-controlled.
    req = make_request(peer="172.18.0.1", xff="6.6.6.6, 203.0.113.9")
    assert get_client_ip(req, trusted_hops=1) == "203.0.113.9"


def test_two_proxy_chain():
    req = make_request(peer="172.18.0.2", xff="6.6.6.6, 203.0.113.9, 172.18.0.1")
    assert get_client_ip(req, trusted_hops=2) == "203.0.113.9"


def test_missing_header_falls_back_to_peer():
    assert get_client_ip(make_request(peer="172.18.0.1"), trusted_hops=1) == "172.18.0.1"


def test_login_rate_limit_cannot_be_bypassed_by_rotating_xff(client):
    codes = []
    for i in range(7):
        r = client.post(
            "/api/v1/auth/login",
            json={"username": "nobody", "password": "wrong-password"},
            headers={"X-Forwarded-For": f"9.9.9.{i}"},
        )
        codes.append(r.status_code)
    assert codes[:5] == [401] * 5
    assert 429 in codes[5:]


def test_login_rate_limit_is_per_username_too(client):
    # Even from "different clients", one account cannot be hammered forever.
    from app.utils import rate_limiter

    for _ in range(10):
        assert rate_limiter.login_user_limiter.is_allowed("victim")
    assert not rate_limiter.login_user_limiter.is_allowed("victim")


# --- limiter behaviour ------------------------------------------------------------

def test_limiter_blocks_after_max_and_frees_memory():
    limiter = SimpleRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.is_allowed("a") and limiter.is_allowed("a")
    assert not limiter.is_allowed("a")
    # A flood of distinct keys must not grow state without bound once they expire.
    limiter.window_seconds = 0
    for i in range(2000):
        limiter.is_allowed(f"k{i}")
    assert len(limiter.requests) < 2000


# --- secrets ----------------------------------------------------------------------

@pytest.mark.parametrize(
    "secret",
    ["", "short", "change-this-in-prod-very-secret", "your-secret-key-change-in-production"],
)
def test_production_rejects_weak_or_published_secret(secret):
    with pytest.raises(ValidationError):
        Settings(ENV="production", SECRET_KEY=secret, DATABASE_URL="postgresql://x/y")


def test_production_accepts_strong_secret():
    s = Settings(ENV="production", SECRET_KEY="k" * 40, DATABASE_URL="postgresql://x/y")
    assert s.is_production


def test_development_allows_weak_secret():
    Settings(ENV="development", SECRET_KEY="dev", DATABASE_URL="postgresql://x/y")


def test_jwt_secret_comes_from_settings():
    from app.core import security
    from app.core.config import settings

    assert security.SECRET_KEY == settings.SECRET_KEY


# --- authentication / password policy ----------------------------------------------

def test_register_rejects_short_password(client):
    r = client.post("/api/v1/auth/register", json={"username": "newdevotee", "password": "short"})
    assert r.status_code == 422


def test_register_always_creates_general_user_even_if_roles_sent(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "sneaky_admin", "password": "long-enough-pw", "roles": ["SUPER_ADMIN"]},
    )
    assert r.status_code == 200
    assert r.json()["roles"] == ["GENERAL_USER"]


def test_deactivated_user_cannot_log_in(client, db):
    from tests.conftest import make_user

    user = make_user(db, ["ADMIN"], username="gone_admin", password="long-enough-pw")
    user.is_active = False
    db.commit()
    r = client.post("/api/v1/auth/login", json={"username": "gone_admin", "password": "long-enough-pw"})
    assert r.status_code == 401


# --- endpoints that must not be public -----------------------------------------------

@pytest.mark.parametrize("path", ["/api/v1/meta/stats", "/api/v1/meta/activity", "/api/v1/donors/1/receipt"])
def test_sensitive_endpoints_require_auth(client, path):
    assert client.get(path).status_code in (401, 403)


def test_announcements_show_all_requires_admin(client, trustee_headers):
    assert client.get("/api/v1/announcements/?show_all=true").status_code == 401
    assert client.get("/api/v1/announcements/?show_all=true", headers=trustee_headers).status_code == 403


def test_general_user_cannot_view_stats(client, db):
    from tests.conftest import make_user, auth_headers

    headers = auth_headers(make_user(db, ["GENERAL_USER"]))
    assert client.get("/api/v1/meta/stats", headers=headers).status_code == 403
