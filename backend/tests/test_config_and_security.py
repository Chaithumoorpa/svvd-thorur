import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.core.config import Settings
from app.utils.rate_limiter import get_client_ip


def _settings(**kw):
    base = dict(DATABASE_URL="sqlite://", SECRET_KEY="k" * 40)
    return Settings(_env_file=None, **{**base, **kw})


def test_production_rejects_weak_secret():
    for secret in ("short", "change-this-in-prod-very-secret", "your-secret-key-change-in-production"):
        with pytest.raises(ValidationError):
            _settings(ENV="production", SECRET_KEY=secret)
    assert _settings(ENV="production").is_production


def test_public_registration_is_off_by_default(monkeypatch):
    monkeypatch.delenv("ALLOW_PUBLIC_REGISTRATION", raising=False)  # conftest enables it for API tests
    assert _settings().ALLOW_PUBLIC_REGISTRATION is False


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError):
        _settings(ENV="production", CORS_ORIGINS="*")


def test_production_defaults_are_hardened_and_dev_is_relaxed():
    prod = _settings(ENV="production")
    assert prod.docs_url is None and prod.security_headers_enabled and prod.rate_limiting_enabled
    dev = _settings(ENV="development")
    assert dev.docs_url == "/docs" and not dev.rate_limiting_enabled
    assert _settings(ENV="production", ENABLE_DOCS="true").docs_url == "/docs"  # explicit override still works


def test_cors_origin_parsing():
    assert _settings(CORS_ORIGINS="https://a.org, https://b.org").CORS_ORIGINS == ["https://a.org", "https://b.org"]
    assert _settings(CORS_ORIGINS='["http://x:3000","http://y:3000"]').CORS_ORIGINS == ["http://x:3000", "http://y:3000"]


def _request(xff=None, client=("10.0.0.9", 1234)):
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "headers": headers, "client": client})


def test_client_ip_ignores_forwarded_header_unless_trusted(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", False)
    assert get_client_ip(_request("6.6.6.6")) == "10.0.0.9"

    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    # attacker prepends a fake address; the proxy appended the real one on the right
    assert get_client_ip(_request("6.6.6.6, 203.0.113.7")) == "203.0.113.7"
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 2)
    assert get_client_ip(_request("6.6.6.6, 203.0.113.7, 10.1.1.1")) == "203.0.113.7"
    assert get_client_ip(_request(None)) == "10.0.0.9"


def test_security_headers_middleware_and_cors_methods(client):
    response = client.options("/api/v1/announcements/", headers={
        "Origin": "http://localhost:3000", "Access-Control-Request-Method": "TRACE"})
    assert response.status_code == 400  # TRACE is not an allowed method
