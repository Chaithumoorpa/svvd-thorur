"""POST /seva-tickets/scan - validates a ticket and marks it USED. A PENDING-
payment ticket (a paid seva booked online, fee not yet collected) is refused
so nobody checks in without paying; the response still carries the ticket so
staff can collect payment right from the scan result."""
import re
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketSource, TicketStatus


def _capture_email(monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.otp_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    _to, _subject, body = sent.call_args[0]
    return re.search(r"\b(\d{6})\b", body).group(1)


def _free_ticket(db) -> SevaTicket:
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    ticket = SevaTicket(
        ticket_number="SVVD-2026-200001", seva_id=pooja.id, seva_name=pooja.name,
        devotee_name="Test Devotee", mobile_number="9999999999", seva_date=date.today(),
        payment_status=PaymentStatus.FREE, amount=0, status=TicketStatus.ACTIVE,
        source=TicketSource.ONLINE, qr_token="scan-tok-free",
    )
    db.add(ticket)
    db.commit()
    return ticket


def _pending_ticket(client, db, monkeypatch):
    pooja = Pooja(name="Abhishekam", pooja_type="special", is_paid=True, suggested_amount=300, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)

    sent = _capture_email(monkeypatch)
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "devotee@example.com"})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": "devotee@example.com", "code": _code_from(sent)}).json()["booking_token"]

    r = client.post("/api/v1/seva-tickets", json={
        "seva_id": pooja.id, "devotee_name": "Lakshmi", "mobile_number": "9876543214",
        "seva_date": (date.today() + timedelta(days=1)).isoformat(),
        "email": "devotee@example.com", "booking_token": token,
    })
    assert r.status_code == 200, r.text
    return r.json()


def test_scan_marks_a_free_ticket_used(client, db, staff):
    _, headers = staff
    ticket = _free_ticket(db)

    r = client.post("/api/v1/seva-tickets/scan", headers=headers, json={"qr_token": ticket.qr_token})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["ticket"]["status"] == "USED"


def test_scan_blocks_a_pending_payment_ticket(client, db, monkeypatch, staff):
    _, headers = staff
    ticket = _pending_ticket(client, db, monkeypatch)

    r = client.post("/api/v1/seva-tickets/scan", headers=headers, json={"qr_token": ticket["qr_token"]})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert "Payment pending" in body["message"]
    assert body["ticket"] is not None
    assert body["ticket"]["payment_status"] == "PENDING"
    assert body["ticket"]["status"] == "ACTIVE"  # not marked used


def test_scan_after_collecting_payment_succeeds(client, db, monkeypatch, staff):
    _, headers = staff
    ticket = _pending_ticket(client, db, monkeypatch)

    blocked = client.post("/api/v1/seva-tickets/scan", headers=headers, json={"qr_token": ticket["qr_token"]})
    assert blocked.json()["success"] is False

    collected = client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert collected.status_code == 200

    r = client.post("/api/v1/seva-tickets/scan", headers=headers, json={"qr_token": ticket["qr_token"]})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["ticket"]["status"] == "USED"


def test_scan_unknown_code_returns_not_found_message(client, staff):
    _, headers = staff
    r = client.post("/api/v1/seva-tickets/scan", headers=headers, json={"qr_token": "no-such-token"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False
    assert body["ticket"] is None
