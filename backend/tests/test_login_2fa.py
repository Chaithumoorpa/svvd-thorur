"""Login is two steps for any account with an email on file: POST /auth/login
(password) returns otp_required and emails a code instead of a session;
POST /auth/login/verify-otp (code) completes it. An account with no email
skips straight to a session - there's nowhere to send a code, and refusing
to log them in would lock real staff out of their own site."""
import re
from unittest.mock import MagicMock


def _capture_email(monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.otp_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    _to, _subject, body = sent.call_args[0]
    return re.search(r"\b(\d{6})\b", body).group(1)


def _login(client, username, password):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def test_login_with_no_email_skips_otp_as_before(client, make_user):
    make_user("ADMIN", username="alice", password="Password123")
    r = _login(client, "alice", "Password123")
    assert r.status_code == 200
    body = r.json()
    assert body["otp_required"] is False
    assert body["access_token"] and body["token_type"] == "bearer"

    verify = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert verify.status_code == 200


def test_login_with_email_requires_otp(client, make_user, monkeypatch):
    sent = _capture_email(monkeypatch)
    make_user("ADMIN", username="bob", password="Password123", email="bob@example.com")

    r = _login(client, "bob", "Password123")
    assert r.status_code == 200
    body = r.json()
    assert body["otp_required"] is True
    assert body.get("access_token") is None
    sent.assert_called_once()
    to_email, subject, _body = sent.call_args[0]
    assert to_email == "bob@example.com" and "sign-in code" in subject.lower()


def test_full_otp_login_round_trip(client, make_user, monkeypatch):
    sent = _capture_email(monkeypatch)
    make_user("STAFF", username="carol", password="Password123", email="carol@example.com")

    step1 = _login(client, "carol", "Password123")
    assert step1.json()["otp_required"] is True
    code = _code_from(sent)

    step2 = client.post("/api/v1/auth/login/verify-otp", json={"username": "carol", "code": code})
    assert step2.status_code == 200, step2.text
    body = step2.json()
    assert body["access_token"] and body["must_change_password"] is False

    verify = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert verify.status_code == 200
    assert verify.json()["username"] == "carol"


def test_wrong_password_never_reaches_otp_step(client, make_user, monkeypatch):
    sent = _capture_email(monkeypatch)
    make_user("ADMIN", username="dana", password="Password123", email="dana@example.com")

    r = _login(client, "dana", "wrong-password")
    assert r.status_code == 401
    sent.assert_not_called()


def test_wrong_otp_code_is_rejected(client, make_user, monkeypatch):
    sent = _capture_email(monkeypatch)
    make_user("ADMIN", username="ellen", password="Password123", email="ellen@example.com")
    _login(client, "ellen", "Password123")
    real_code = _code_from(sent)
    wrong_code = f"{(int(real_code) + 1) % 1_000_000:06d}"

    r = client.post("/api/v1/auth/login/verify-otp", json={"username": "ellen", "code": wrong_code})
    assert r.status_code == 400


def test_otp_code_is_single_use(client, make_user, monkeypatch):
    sent = _capture_email(monkeypatch)
    make_user("ADMIN", username="frank", password="Password123", email="frank@example.com")
    _login(client, "frank", "Password123")
    code = _code_from(sent)

    first = client.post("/api/v1/auth/login/verify-otp", json={"username": "frank", "code": code})
    assert first.status_code == 200

    second = client.post("/api/v1/auth/login/verify-otp", json={"username": "frank", "code": code})
    assert second.status_code == 400


def test_a_booking_code_cannot_be_used_to_log_in(client, db, make_user, monkeypatch):
    """Booking and login codes are scoped by purpose so one can never verify the other,
    even for the exact same email address."""
    sent = _capture_email(monkeypatch)
    make_user("ADMIN", username="grace", password="Password123", email="grace@example.com")

    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "grace@example.com"})
    booking_code = _code_from(sent)

    r = client.post("/api/v1/auth/login/verify-otp", json={"username": "grace", "code": booking_code})
    assert r.status_code == 400


def test_login_otp_is_rate_limited_per_ip(client, make_user, monkeypatch):
    _capture_email(monkeypatch)
    make_user("ADMIN", username="henry", password="Password123", email="henry@example.com")
    statuses = [_login(client, "henry", "wrong").status_code for _ in range(7)]
    assert statuses[:5] == [401] * 5
    assert 429 in statuses[5:]
