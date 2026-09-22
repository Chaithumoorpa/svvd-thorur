"""Online seva booking is gated on a verified email: request-otp emails a
6-digit code, verify-otp exchanges it for a short-lived booking_token, and
the actual booking endpoint requires that token to match the booking's email.
EmailService.send is mocked to capture the emailed code (SES isn't configured
in tests) so these exercise the full HTTP round trip, not just the service."""
import re
from unittest.mock import MagicMock

from app.models.pooja import Pooja


def _capture_email(monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.otp_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    _to, _subject, body = sent.call_args[0]
    return re.search(r"\b(\d{6})\b", body).group(1)


def test_request_and_verify_otp_round_trip(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    r = client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "devotee@example.com"})
    assert r.status_code == 200
    sent.assert_called_once()

    verify = client.post("/api/v1/seva-tickets/booking/verify-otp",
                         json={"email": "devotee@example.com", "code": _code_from(sent)})
    assert verify.status_code == 200
    assert verify.json()["booking_token"]


def test_verify_otp_wrong_code_rejected(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "devotee2@example.com"})
    wrong_code = f"{(int(_code_from(sent)) + 1) % 1_000_000:06d}"

    r = client.post("/api/v1/seva-tickets/booking/verify-otp",
                    json={"email": "devotee2@example.com", "code": wrong_code})
    assert r.status_code == 400


def test_verify_otp_without_request_fails(client):
    r = client.post("/api/v1/seva-tickets/booking/verify-otp",
                    json={"email": "nobody@example.com", "code": "123456"})
    assert r.status_code == 400


def test_verify_otp_locks_out_after_max_attempts(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "devotee3@example.com"})
    real_code = _code_from(sent)
    wrong_code = f"{(int(real_code) + 1) % 1_000_000:06d}"

    for _ in range(5):
        r = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": "devotee3@example.com", "code": wrong_code})
        assert r.status_code == 400

    # even the correct code is now rejected - the code is dead after 5 wrong guesses
    locked = client.post("/api/v1/seva-tickets/booking/verify-otp",
                         json={"email": "devotee3@example.com", "code": real_code})
    assert locked.status_code == 400


def test_otp_request_is_rate_limited(client, monkeypatch):
    _capture_email(monkeypatch)
    statuses = [client.post("/api/v1/seva-tickets/booking/request-otp",
                            json={"email": "flood@example.com"}).status_code for _ in range(6)]
    assert statuses[:5] == [200] * 5
    assert 429 in statuses[5:]


def _seva(db) -> Pooja:
    pooja = Pooja(name="Free Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    return pooja


def _booking_payload(seva, email, token, mobile="9876543210"):
    from datetime import date, timedelta
    return {
        "seva_id": seva.id, "devotee_name": "Ravi", "mobile_number": mobile,
        "seva_date": (date.today() + timedelta(days=1)).isoformat(),
        "email": email, "booking_token": token,
    }


def test_booking_requires_a_booking_token(client, db):
    seva = _seva(db)
    payload = _booking_payload(seva, "ravi@example.com", "not-a-real-token")
    r = client.post("/api/v1/seva-tickets", json=payload)
    assert r.status_code == 400


def test_booking_rejects_token_issued_for_a_different_email(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    seva = _seva(db)

    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "someone-else@example.com"})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": "someone-else@example.com", "code": _code_from(sent)}).json()["booking_token"]

    payload = _booking_payload(seva, "ravi@example.com", token)  # different email than the token was issued for
    r = client.post("/api/v1/seva-tickets", json=payload)
    assert r.status_code == 400


def test_booking_succeeds_with_a_valid_verified_token(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    seva = _seva(db)

    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "ravi@example.com"})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": "ravi@example.com", "code": _code_from(sent)}).json()["booking_token"]

    payload = _booking_payload(seva, "ravi@example.com", token)
    r = client.post("/api/v1/seva-tickets", json=payload)
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "ravi@example.com"
    # a confirmation email was sent in addition to the OTP code email
    assert sent.call_count == 2
    to_email, subject, _body = sent.call_args_list[-1][0]
    assert to_email == "ravi@example.com" and "Booking confirmed" in subject
