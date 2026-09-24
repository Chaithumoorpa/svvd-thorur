"""DELETE /auth/me - a devotee deleting their own account (DPDPA right to
erasure). Unlinks rather than deletes anything with its own independent
record (seva tickets, a linked Member row), discards ephemeral security
data (password reset tokens), and is off-limits to staff/admin accounts."""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from app.core.security import hash_password
from app.models.member import Member
from app.models.password_reset import PasswordResetToken
from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus
from app.models.user import User


def _devotee(db, username="devotee1", password="Password123"):
    user = User(username=username, hashed_password=hash_password(password),
                roles=["GENERAL_USER"], email=f"{username}@example.com", phone="9876543210")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers_for(user):
    from app.core.security import create_access_token
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


def test_devotee_can_delete_own_account(client, db, monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.api.v1.auth.EmailService.send", sent)
    user = _devotee(db)
    headers = _headers_for(user)

    r = client.request("DELETE", "/api/v1/auth/me", headers=headers, json={"password": "Password123"})
    assert r.status_code == 200, r.text
    assert db.query(User).filter(User.username == "devotee1").first() is None
    sent.assert_called_once()
    to_email, subject, _body = sent.call_args[0]
    assert to_email == "devotee1@example.com" and "deleted" in subject.lower()


def test_delete_account_requires_correct_password(client, db):
    user = _devotee(db)
    headers = _headers_for(user)

    r = client.request("DELETE", "/api/v1/auth/me", headers=headers, json={"password": "wrong"})
    assert r.status_code == 401
    assert db.query(User).filter(User.id == user.id).first() is not None


def test_staff_and_admin_cannot_self_delete_this_way(client, staff, admin, super_admin):
    for _, headers in (staff, admin, super_admin):
        r = client.request("DELETE", "/api/v1/auth/me", headers=headers, json={"password": "Password123"})
        assert r.status_code == 403


def test_deleting_account_unlinks_but_keeps_booked_tickets(client, db):
    user = _devotee(db, username="devotee2")
    headers = _headers_for(user)
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    ticket = SevaTicket(
        ticket_number="SVVD-2026-300001", seva_id=pooja.id, seva_name=pooja.name,
        devotee_name="Devotee Two", mobile_number="9876543210", seva_date=date.today() + timedelta(days=1),
        payment_status=PaymentStatus.FREE, amount=0, status=TicketStatus.ACTIVE,
        source=TicketSource.ONLINE, qr_token="del-tok-1", booked_by_user_id=user.id,
    )
    db.add(ticket)
    db.commit()

    r = client.request("DELETE", "/api/v1/auth/me", headers=headers, json={"password": "Password123"})
    assert r.status_code == 200, r.text

    db.expire_all()
    kept = db.query(SevaTicket).filter(SevaTicket.ticket_number == "SVVD-2026-300001").one()
    assert kept.booked_by_user_id is None
    assert kept.devotee_name == "Devotee Two"  # the ticket's own record is untouched


def test_deleting_account_unlinks_a_member_row_and_discards_reset_tokens(client, db):
    user = _devotee(db, username="devotee3")
    headers = _headers_for(user)
    member = Member(name="Devotee Three", phone="9876543210", user_id=user.id)
    db.add(member)
    db.add(PasswordResetToken(user_id=user.id, token_hash="x" * 64,
                              expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.commit()
    member_id = member.id

    r = client.request("DELETE", "/api/v1/auth/me", headers=headers, json={"password": "Password123"})
    assert r.status_code == 200, r.text

    db.expire_all()
    assert db.query(Member).filter(Member.id == member_id).one().user_id is None
    assert db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).count() == 0
