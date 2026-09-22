import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from app.models.password_reset import PasswordResetToken
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService


def _login(client, username, password):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_login_success_and_verify(client, make_user):
    make_user("ADMIN", username="alice", password="Password123")
    response = _login(client, "alice", "Password123")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer" and body["must_change_password"] is False

    verify = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert verify.status_code == 200
    data = verify.json()
    assert data["is_admin"] is True and data["is_super_admin"] is False
    assert "content:write" in data["permissions"] and "users:manage" not in data["permissions"]


def test_login_failures_are_indistinguishable(client, make_user):
    make_user("ADMIN", username="alice", password="Password123")
    wrong_pw = _login(client, "alice", "nope")
    unknown = _login(client, "ghost", "nope")
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()


def test_inactive_user_cannot_login(client, db, make_user):
    user, _ = make_user("ADMIN", username="bob", password="Password123")
    user.is_active = False
    db.commit()
    assert _login(client, "bob", "Password123").status_code == 401


def test_login_rate_limited(client, make_user):
    make_user("ADMIN", username="alice", password="Password123")
    statuses = [_login(client, "alice", "wrong").status_code for _ in range(7)]
    assert statuses[:5] == [401] * 5
    assert 429 in statuses[5:]


def test_register_creates_general_user_only(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "devotee1", "password": "Temple123", "roles": ["SUPER_ADMIN"], "is_admin": True,
    })
    assert response.status_code == 201
    assert response.json()["roles"] == ["GENERAL_USER"]


@pytest.mark.parametrize("password", ["short1", "allletters", "12345678"])
def test_weak_passwords_rejected(client, password):
    response = client.post("/api/v1/auth/register", json={"username": "devotee2", "password": password})
    assert response.status_code == 422


def test_duplicate_username_and_email(client):
    ok = {"username": "devotee3", "password": "Temple123", "email": "a@example.com"}
    assert client.post("/api/v1/auth/register", json=ok).status_code == 201
    assert client.post("/api/v1/auth/register", json=ok).status_code == 400
    other = {**ok, "username": "devotee4"}
    assert client.post("/api/v1/auth/register", json=other).status_code == 400  # same email


def test_registration_can_be_disabled(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ALLOW_PUBLIC_REGISTRATION", False)
    assert client.post("/api/v1/auth/register",
                       json={"username": "devotee5", "password": "Temple123"}).status_code == 403


def test_change_password(client, make_user):
    _, headers = make_user("STAFF", username="carol", password="Password123")
    bad = client.post("/api/v1/auth/change-password", headers=headers,
                      json={"current_password": "wrong", "new_password": "NewPass456"})
    assert bad.status_code == 401
    same = client.post("/api/v1/auth/change-password", headers=headers,
                       json={"current_password": "Password123", "new_password": "Password123"})
    assert same.status_code == 400
    ok = client.post("/api/v1/auth/change-password", headers=headers,
                     json={"current_password": "Password123", "new_password": "NewPass456"})
    assert ok.status_code == 200
    assert _login(client, "carol", "NewPass456").status_code == 200


def test_super_admin_creates_user_who_must_change_password(client, super_admin):
    _, headers = super_admin
    response = client.post("/api/v1/auth/admin/users", headers=headers, json={
        "username": "priest1", "password": "Temp12345", "roles": ["STAFF", "STAFF"]})
    assert response.status_code == 201
    assert response.json()["roles"] == ["STAFF"] and response.json()["must_change_password"] is True
    assert _login(client, "priest1", "Temp12345").json()["must_change_password"] is True


def test_cannot_lock_out_last_super_admin_or_self(client, super_admin, make_user):
    root, headers = super_admin
    own = client.patch(f"/api/v1/auth/admin/users/{root.id}", headers=headers, json={"is_active": False})
    assert own.status_code == 400

    other, other_headers = make_user("SUPER_ADMIN", username="root2")
    # another super admin exists, so demoting root2 by root is fine
    ok = client.patch(f"/api/v1/auth/admin/users/{other.id}", headers=headers, json={"roles": ["ADMIN"]})
    assert ok.status_code == 200
    # ...but now root is the only one; a second super admin cannot be demoted by a non-super admin either
    admin_user, admin_headers = make_user("ADMIN", username="adm")
    assert client.patch(f"/api/v1/auth/admin/users/{root.id}", headers=admin_headers,
                        json={"roles": ["GENERAL_USER"]}).status_code == 403


def test_admin_reset_password_forces_change(client, super_admin, make_user):
    _, headers = super_admin
    target, _ = make_user("STAFF", username="dave", password="Password123")
    assert client.patch(f"/api/v1/auth/admin/users/{target.id}", headers=headers,
                        json={"password": "Reset12345"}).status_code == 200
    assert _login(client, "dave", "Password123").status_code == 401
    assert _login(client, "dave", "Reset12345").json()["must_change_password"] is True


def test_forgot_password_unknown_email_is_silent(client):
    r = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 200
    assert "sent" in r.json()["message"].lower()


def test_forgot_password_and_reset_flow(client, db, make_user):
    make_user("STAFF", username="erin", password="Password123", email="erin@example.com")
    assert client.post("/api/v1/auth/forgot-password", json={"email": "erin@example.com"}).status_code == 200

    # the raw token only ever exists in the email; issue one the same way the
    # endpoint did (it's disabled in tests since no SES config is set) to test the confirm step
    service = AuthService(UserRepository(db))
    result = service.request_password_reset("erin@example.com")
    assert result is not None
    _, raw_token = result

    reset = client.post("/api/v1/auth/reset-password", json={"token": raw_token, "new_password": "Fresh12345"})
    assert reset.status_code == 200
    assert _login(client, "erin", "Fresh12345").status_code == 200

    # single-use: the same token cannot be replayed
    reuse = client.post("/api/v1/auth/reset-password", json={"token": raw_token, "new_password": "Another123"})
    assert reuse.status_code == 400


def test_reset_password_invalid_token(client):
    r = client.post("/api/v1/auth/reset-password", json={"token": "not-a-real-token", "new_password": "Whatever123"})
    assert r.status_code == 400


def test_reset_password_expired_token(client, db, make_user):
    make_user("STAFF", username="frank", password="Password123", email="frank@example.com")
    service = AuthService(UserRepository(db))
    _, raw_token = service.request_password_reset("frank@example.com")

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    record = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    record.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db.commit()

    r = client.post("/api/v1/auth/reset-password", json={"token": raw_token, "new_password": "Whatever123"})
    assert r.status_code == 400


def test_forgot_password_rate_limited(client, make_user):
    make_user("STAFF", username="grace", password="Password123", email="grace@example.com")
    statuses = [client.post("/api/v1/auth/forgot-password", json={"email": "grace@example.com"}).status_code
                for _ in range(6)]
    assert statuses[:5] == [200] * 5
    assert 429 in statuses[5:]
