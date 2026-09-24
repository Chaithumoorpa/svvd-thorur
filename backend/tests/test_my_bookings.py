"""GET /seva-tickets/mine - a signed-in devotee's own booking history. Only
tickets booked while signed in are linked (see test_booking_otp.py), so this
just covers auth and per-user filtering/ordering over already-linked tickets."""
from datetime import date

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus


def _seva(db) -> Pooja:
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    return pooja


def _ticket(db, seva, number, booked_by_user_id=None) -> SevaTicket:
    ticket = SevaTicket(
        ticket_number=number, seva_id=seva.id, seva_name=seva.name,
        devotee_name="Test Devotee", mobile_number="9999999999", seva_date=date.today(),
        payment_status=PaymentStatus.FREE, amount=0, status=TicketStatus.ACTIVE,
        source=TicketSource.ONLINE, qr_token=f"tok-{number}", booked_by_user_id=booked_by_user_id,
    )
    db.add(ticket)
    db.commit()
    return ticket


def test_mine_requires_authentication(client):
    r = client.get("/api/v1/seva-tickets/mine")
    assert r.status_code == 401


def test_mine_returns_only_the_caller_own_tickets(client, db, make_user):
    seva = _seva(db)
    devotee, headers = make_user("GENERAL_USER", username="devotee1")
    other, other_headers = make_user("GENERAL_USER", username="devotee2")
    _ticket(db, seva, "SVVD-2026-100001", booked_by_user_id=devotee.id)
    _ticket(db, seva, "SVVD-2026-100002", booked_by_user_id=other.id)
    _ticket(db, seva, "SVVD-2026-100003", booked_by_user_id=None)  # anonymous booking

    r = client.get("/api/v1/seva-tickets/mine", headers=headers)
    assert r.status_code == 200
    numbers = [t["ticket_number"] for t in r.json()]
    assert numbers == ["SVVD-2026-100001"]

    r_other = client.get("/api/v1/seva-tickets/mine", headers=other_headers)
    assert [t["ticket_number"] for t in r_other.json()] == ["SVVD-2026-100002"]
