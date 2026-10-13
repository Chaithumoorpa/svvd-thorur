"""Browser sessions: an HttpOnly cookie instead of a token page JavaScript can
read, revocable (logout / password change / reset / deactivation end every
existing token), typed (a booking token is not a login), CSRF-guarded for
cookie-authenticated writes, and capped at SESSION_MAX_HOURS however often
it is refreshed."""
import time

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService, issue_session_token
from app.services.otp_service import BOOKING_PURPOSE, OtpService

VERIFY = "/api/v1/auth/verify"
CSRF = {"X-Requested-With": "XMLHttpRequest"}


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _login(client, username):
    r = client.post("/api/v1/auth/login", json={"username": username, "password": "Password123"})
    assert r.status_code == 200, r.text
    return r


def test_session_cookie_is_httponly_strict_and_scoped_to_the_api(client, make_user):
    make_user("ADMIN", username="alice")
    cookie = _login(client, "alice").headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "path=/api/v1" in cookie
    assert f"max-age={settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60}" in cookie
    assert "secure" not in cookie  # plain-http local dev


def test_session_cookie_is_secure_in_production(client, make_user, monkeypatch):
    make_user("ADMIN", username="alice")
    monkeypatch.setattr(settings, "ENV", "production")
    assert "secure" in _login(client, "alice").headers["set-cookie"].lower()


def test_cookie_authenticated_writes_need_the_csrf_header(client, make_user):
    make_user("ADMIN", username="alice")
    _login(client, "alice")
    assert client.get(VERIFY).status_code == 200  # reads don't
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 403 and "X-Requested-With" in r.json()["detail"]
    assert client.post("/api/v1/auth/refresh", headers=CSRF).status_code == 200


def test_logout_ends_every_session_including_stolen_copies(client, make_user):
    user, other_device = make_user("ADMIN", username="alice")
    _login(client, "alice")
    stolen = client.cookies.get("svvd_session")

    r = client.post("/api/v1/auth/logout", headers=CSRF)
    assert r.status_code == 200
    assert 'svvd_session=""' in r.headers["set-cookie"] or "max-age=0" in r.headers["set-cookie"].lower()
    assert client.get(VERIFY).status_code == 401
    assert client.get(VERIFY, headers=_bearer(stolen)).status_code == 401
    assert client.get(VERIFY, headers=other_device).status_code == 401


def test_logout_without_a_session_still_succeeds(client):
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200 and "svvd_session" in r.headers["set-cookie"]


def test_password_change_keeps_this_device_and_signs_out_the_others(client, db, make_user):
    user, this_device = make_user("ADMIN", username="alice")
    other_device = _bearer(issue_session_token(user))
    r = client.post("/api/v1/auth/change-password", headers=this_device,
                    json={"current_password": "Password123", "new_password": "NewPassword456"})
    assert r.status_code == 200, r.text
    assert client.get(VERIFY).status_code == 200  # via the fresh cookie the response set
    assert client.get(VERIFY, headers=other_device).status_code == 401
    assert client.get(VERIFY, headers=this_device).status_code == 401  # the pre-change token too


def test_password_reset_ends_existing_sessions(client, db, make_user):
    _, headers = make_user("ADMIN", username="alice", email="alice@example.com")
    _, raw = AuthService(UserRepository(db)).request_password_reset("alice@example.com")
    r = client.post("/api/v1/auth/reset-password", json={"token": raw, "new_password": "NewPassword456"})
    assert r.status_code == 200, r.text
    assert client.get(VERIFY, headers=headers).status_code == 401


def test_reactivating_a_user_does_not_revive_old_tokens(client, make_user):
    _, admin = make_user("SUPER_ADMIN", username="boss")
    target, target_headers = make_user("STAFF", username="carol")
    url = f"/api/v1/auth/admin/users/{target.id}"
    assert client.patch(url, headers=admin, json={"is_active": False}).status_code == 200
    assert client.patch(url, headers=admin, json={"is_active": True}).status_code == 200
    assert client.get(VERIFY, headers=target_headers).status_code == 401


def test_a_booking_token_is_not_a_login(client, make_user):
    user, _ = make_user("GENERAL_USER", username="dev", email="dev@example.com")
    booking = create_access_token({"typ": "booking", "purpose": BOOKING_PURPOSE, "email": "dev@example.com",
                                   "user_id": user.id})
    assert client.get(VERIFY, headers=_bearer(booking)).status_code == 401


def test_a_login_token_is_not_a_booking_token(db, make_user):
    import pytest
    from fastapi import HTTPException

    user, _ = make_user("GENERAL_USER", username="dev", email="dev@example.com")
    with pytest.raises(HTTPException):
        OtpService.check_booking_token(issue_session_token(user), "dev@example.com")


def test_tokens_from_before_this_change_are_rejected(client, make_user):
    user, _ = make_user("ADMIN", username="alice")
    legacy = create_access_token({"sub": user.username, "user_id": user.id})  # no typ/ver/auth_time
    assert client.get(VERIFY, headers=_bearer(legacy)).status_code == 401


def test_sessions_end_after_the_maximum_length(client, make_user):
    user, _ = make_user("ADMIN", username="alice")
    too_old = int(time.time()) - settings.SESSION_MAX_HOURS * 3600 - 60
    token = issue_session_token(user, auth_time=too_old)
    assert client.get(VERIFY, headers=_bearer(token)).status_code == 401
    assert client.post("/api/v1/auth/refresh", headers=_bearer(token)).status_code == 401


def test_refreshing_keeps_the_original_sign_in_time(client, make_user):
    user, _ = make_user("ADMIN", username="alice")
    signed_in_at = int(time.time()) - 3600
    r = client.post("/api/v1/auth/refresh", headers=_bearer(issue_session_token(user, auth_time=signed_in_at)))
    assert r.status_code == 200
    assert decode_access_token(client.cookies.get("svvd_session"))["auth_time"] == signed_in_at
