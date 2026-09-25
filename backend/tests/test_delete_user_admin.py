"""DELETE /auth/admin/users/{id} - Super Admin deleting any account (staff,
admin, or a devotee who never got around to self-deleting). Same
never-yourself, never-the-last-Super-Admin protections update_user already
enforces, and the same unlink-not-orphan treatment self-deletion uses."""
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService


def _delete(client, headers, user_id):
    return client.delete(f"/api/v1/auth/admin/users/{user_id}", headers=headers)


def test_super_admin_can_delete_a_staff_account(client, super_admin, make_user):
    _, headers = super_admin
    target, _ = make_user("STAFF", username="fired_staff")

    r = _delete(client, headers, target.id)
    assert r.status_code == 200, r.text


def test_admin_cannot_delete_users(client, admin, make_user):
    _, headers = admin
    target, _ = make_user("STAFF", username="someone")

    r = _delete(client, headers, target.id)
    assert r.status_code == 403


def test_cannot_delete_your_own_account_here(client, super_admin):
    root, headers = super_admin
    r = _delete(client, headers, root.id)
    assert r.status_code == 400


def test_cannot_delete_the_last_active_super_admin(db, make_user):
    """The only way to reach this guard through the HTTP API is a Super Admin
    acting on themselves, which the separate self-delete check already blocks
    first - exercised here at the service layer instead, same as update_user's
    analogous check for deactivating/demoting the last one."""
    root, _ = make_user("SUPER_ADMIN", username="only_root")
    other, _ = make_user("ADMIN", username="not_super")
    service = AuthService(UserRepository(db))

    with pytest.raises(HTTPException) as exc:
        service.delete_user(root.id, acting_user=other)
    assert exc.value.status_code == 400


def test_deleting_a_user_unlinks_their_booked_tickets(client, db, super_admin, make_user):
    _, headers = super_admin
    devotee, _ = make_user("GENERAL_USER", username="devotee_x")
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    ticket = SevaTicket(
        ticket_number="SVVD-2026-400001", seva_id=pooja.id, seva_name=pooja.name,
        devotee_name="Devotee X", mobile_number="9876543215", seva_date=date.today() + timedelta(days=1),
        payment_status=PaymentStatus.FREE, amount=0, status=TicketStatus.ACTIVE,
        source=TicketSource.ONLINE, qr_token="del-admin-tok-1", booked_by_user_id=devotee.id,
    )
    db.add(ticket)
    db.commit()

    r = _delete(client, headers, devotee.id)
    assert r.status_code == 200, r.text

    db.expire_all()
    kept = db.query(SevaTicket).filter(SevaTicket.ticket_number == "SVVD-2026-400001").one()
    assert kept.booked_by_user_id is None


def test_delete_user_requires_authentication(client):
    assert _delete(client, {}, 1).status_code == 401
