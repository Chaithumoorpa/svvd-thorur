"""Abuse resistance around accounts: per-account login limit, reset-email cap,
verified-only bulk mail, and clearing out sign-ups that never proved their email."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.models.audit_log import AuditLog
from app.models.member import Member
from app.models.pooja import Pooja
from app.models.seva_ticket import SevaTicket
from app.models.user import User


def test_password_guessing_is_limited_per_account_not_just_per_ip(client, make_user):
    from app.utils import rate_limiter
    make_user("ADMIN", username="target", password="Password123")
    statuses = []
    for n in range(11):
        rate_limiter.login_limiter.requests.clear()   # as if every guess came from a different IP
        statuses.append(client.post("/api/v1/auth/login",
                                    json={"username": "target", "password": f"guess{n}x"}).status_code)
    assert statuses[:10] == [401] * 10 and statuses[10] == 429
    rate_limiter.login_limiter.requests.clear()
    # even the right password waits now - and the limit is keyed on what was typed, case-insensitively
    r = client.post("/api/v1/auth/login", json={"username": "Target", "password": "Password123"})
    assert r.status_code == 429 and "this account" in r.json()["detail"]


def test_reset_emails_to_one_account_are_capped(client, make_user, monkeypatch):
    sent = MagicMock(return_value=True)
    monkeypatch.setattr("app.api.v1.auth.EmailService.send", sent)
    make_user("STAFF", username="resetme", email="resetme@example.com")
    for _ in range(5):
        r = client.post("/api/v1/auth/forgot-password", json={"email": "resetme@example.com"})
        assert r.status_code == 200 and "If that email is registered" in r.json()["message"]
    assert sent.call_count == 3


def test_sign_in_code_marks_the_email_verified(client, db, make_user, monkeypatch):
    sent = MagicMock(return_value=True)
    monkeypatch.setattr("app.services.otp_service.EmailService.send", sent)
    user, _ = make_user("GENERAL_USER", username="oldsignup", email="old@example.com", email_verified_at=None)
    client.post("/api/v1/auth/login", json={"username": "oldsignup", "password": "Password123"})
    code = sent.call_args.kwargs["code"]
    assert client.post("/api/v1/auth/login/verify-otp", json={"username": "oldsignup", "code": code}).status_code == 200
    db.refresh(user)
    assert user.email_verified_at is not None


def test_devotee_notices_skip_unverified_addresses(client, admin, make_user, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.notification_service.EmailService.send", sent)
    make_user("GENERAL_USER", username="real", email="real@example.com")
    make_user("GENERAL_USER", username="fake", email="fake@example.com", email_verified_at=None)
    _, headers = admin
    client.post("/api/v1/temple/timings", headers=headers,
                json={"label": "Evening Aarti", "start_time": "18:00:00", "end_time": "19:00:00"})
    assert {c.args[0] for c in sent.call_args_list} == {"real@example.com"}


def test_super_admin_can_clear_out_unverified_signups(client, db, make_user, super_admin, admin):
    old = datetime.utcnow() - timedelta(days=3)
    spam, _ = make_user("GENERAL_USER", username="spam1", email="spam1@example.com", email_verified_at=None,
                        created_at=old)
    booked, _ = make_user("GENERAL_USER", username="booked", email="b@example.com", email_verified_at=None,
                          created_at=old)
    pooja = Pooja(name="Abhishekam", pooja_type="special", is_active=True)
    db.add(pooja)
    db.flush()
    db.add(SevaTicket(ticket_number="SV-X-1", seva_id=pooja.id, seva_name="Abhishekam", devotee_name="B",
                      mobile_number="9876543210", seva_date=datetime.utcnow().date(), qr_token="qr-test-1",
                      booked_by_user_id=booked.id))
    linked, _ = make_user("GENERAL_USER", username="member", email="m@example.com", email_verified_at=None,
                          created_at=old)
    db.add(Member(name="Member", phone="9000000009", user_id=linked.id))
    make_user("GENERAL_USER", username="fresh", email="f@example.com", email_verified_at=None)   # < 1 day old
    make_user("STAFF", username="staffer", email="s@example.com", email_verified_at=None, created_at=old)
    db.commit()

    _, root = super_admin
    _, admin_h = admin
    assert client.get("/api/v1/auth/admin/users/unverified", headers=admin_h).status_code == 403
    listed = client.get("/api/v1/auth/admin/users/unverified", headers=root).json()
    assert [u["username"] for u in listed] == ["spam1"]
    assert client.post("/api/v1/auth/admin/users/purge-unverified", headers=root).json() == {"deleted": 1}
    assert db.query(User).filter_by(username="spam1").count() == 0
    assert {u.username for u in db.query(User).all()} >= {"booked", "member", "fresh", "staffer"}
    log = db.query(AuditLog).filter_by(action="PURGE_UNVERIFIED").one()
    assert log.changes == {"usernames": ["spam1"]}
