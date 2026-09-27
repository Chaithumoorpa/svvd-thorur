"""TurnstileService itself, plus its wiring into login/register/forgot-password.
Unconfigured (no TURNSTILE_SECRET_KEY, the default in every other test in this
suite) it's a no-op - every other test file's auth flows keep working unchanged."""
from unittest.mock import MagicMock

import httpx
import pytest

from app.services.turnstile_service import TurnstileService


def test_disabled_when_no_secret_configured():
    service = TurnstileService()
    assert service.enabled is False
    assert service.verify(None) is True  # no token needed - not gated at all
    assert service.verify("anything") is True


def test_enabled_requires_a_token(monkeypatch):
    monkeypatch.setattr("app.services.turnstile_service.settings.TURNSTILE_SECRET_KEY", "secret")
    service = TurnstileService()
    assert service.enabled is True
    assert service.verify(None) is False
    assert service.verify("") is False


def test_enabled_accepts_a_verified_token(monkeypatch):
    monkeypatch.setattr("app.services.turnstile_service.settings.TURNSTILE_SECRET_KEY", "secret")
    response = MagicMock()
    response.json.return_value = {"success": True}
    monkeypatch.setattr("httpx.post", MagicMock(return_value=response))
    assert TurnstileService().verify("good-token") is True


def test_enabled_rejects_a_failed_challenge(monkeypatch):
    monkeypatch.setattr("app.services.turnstile_service.settings.TURNSTILE_SECRET_KEY", "secret")
    response = MagicMock()
    response.json.return_value = {"success": False, "error-codes": ["invalid-input-response"]}
    monkeypatch.setattr("httpx.post", MagicMock(return_value=response))
    assert TurnstileService().verify("bad-token") is False


def test_enabled_fails_closed_on_verification_error(monkeypatch):
    """Unlike email (best-effort, must never block), the challenge IS the
    gate - a Cloudflare outage or timeout must not let an attacker through."""
    monkeypatch.setattr("app.services.turnstile_service.settings.TURNSTILE_SECRET_KEY", "secret")
    monkeypatch.setattr("httpx.post", MagicMock(side_effect=httpx.ConnectError("boom")))
    assert TurnstileService().verify("some-token") is False


# ------------------------------------------------------------------------- wiring


def _configure_turnstile(monkeypatch, passes: bool):
    monkeypatch.setattr("app.services.turnstile_service.settings.TURNSTILE_SECRET_KEY", "secret")
    monkeypatch.setattr("app.services.turnstile_service.TurnstileService.verify", lambda self, *a, **k: passes)


def test_login_requires_turnstile_when_configured(client, admin, monkeypatch):
    _, headers = admin
    _configure_turnstile(monkeypatch, passes=False)
    r = client.post("/api/v1/auth/login", json={"username": "unused", "password": "wrong"})
    assert r.status_code == 400
    assert "Security check" in r.json()["detail"]


def test_login_proceeds_once_turnstile_passes(client, make_user, monkeypatch):
    user, _ = make_user("STAFF", username="turnstile_ok", password="Password123")
    _configure_turnstile(monkeypatch, passes=True)
    r = client.post("/api/v1/auth/login", json={"username": "turnstile_ok", "password": "Password123"})
    assert r.status_code == 200, r.text  # no email on file - single factor, straight to a token


def test_register_requires_turnstile_when_configured(client, monkeypatch):
    _configure_turnstile(monkeypatch, passes=False)
    r = client.post("/api/v1/auth/register", json={
        "username": "newdevotee", "email": "newdevotee@example.com", "phone": "9876543210",
        "password": "Password123",
    })
    assert r.status_code == 400
    assert "Security check" in r.json()["detail"]


def test_forgot_password_requires_turnstile_when_configured(client, monkeypatch):
    _configure_turnstile(monkeypatch, passes=False)
    r = client.post("/api/v1/auth/forgot-password", json={"email": "someone@example.com"})
    assert r.status_code == 400
    assert "Security check" in r.json()["detail"]


def test_contact_form_requires_turnstile_when_configured(client, monkeypatch):
    _configure_turnstile(monkeypatch, passes=False)
    r = client.post("/api/v1/contacts", json={
        "name": "Dev A", "email": "dev@example.com", "subject": "Timing query",
        "message": "When is the evening pooja?",
    })
    assert r.status_code == 400
    assert "Security check" in r.json()["detail"]


def test_seva_booking_requires_turnstile_when_configured(client, monkeypatch):
    _configure_turnstile(monkeypatch, passes=False)
    r = client.post("/api/v1/seva-tickets", json={
        "seva_id": 1, "devotee_name": "Ravi", "mobile_number": "9876543210",
        "seva_date": "2027-01-01", "email": "ravi@example.com", "booking_token": "irrelevant",
    })
    assert r.status_code == 400
    assert "Security check" in r.json()["detail"]
