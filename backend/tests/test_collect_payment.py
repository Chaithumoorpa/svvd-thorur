"""Collecting payment for a PENDING ticket (a paid seva booked online, fee not
yet collected) - the counter-side half of booking a paid seva without a
payment gateway: pay in person, staff marks it collected."""
from datetime import date, timedelta
from unittest.mock import MagicMock

import re

from app.models.finance import IncomeTransaction
from app.models.pooja import Pooja


def _capture_email(monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.otp_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    _to, _subject, body = sent.call_args[0]
    return re.search(r"\b(\d{6})\b", body).group(1)


def _pending_ticket(client, db, monkeypatch, mobile="9876543212"):
    pooja = Pooja(name="Abhishekam", pooja_type="special", is_paid=True, suggested_amount=250, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)

    sent = _capture_email(monkeypatch)
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "devotee@example.com"})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": "devotee@example.com", "code": _code_from(sent)}).json()["booking_token"]

    r = client.post("/api/v1/seva-tickets", json={
        "seva_id": pooja.id, "devotee_name": "Lakshmi", "mobile_number": mobile,
        "seva_date": (date.today() + timedelta(days=1)).isoformat(),
        "email": "devotee@example.com", "booking_token": token,
    })
    assert r.status_code == 200, r.text
    return r.json()


def test_staff_can_collect_payment_for_a_pending_ticket(client, db, monkeypatch, staff):
    _, headers = staff
    ticket = _pending_ticket(client, db, monkeypatch)
    assert ticket["payment_status"] == "PENDING"

    r = client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["payment_status"] == "PAID"

    income = db.query(IncomeTransaction).filter_by(reference_id=f"seva_ticket:{ticket['id']}").one()
    assert income.amount == 250


def test_collect_payment_requires_tickets_manage_permission(client, db, monkeypatch, trustee):
    _, headers = trustee
    ticket = _pending_ticket(client, db, monkeypatch)
    r = client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert r.status_code == 403


def test_cannot_collect_payment_twice(client, db, monkeypatch, staff):
    _, headers = staff
    ticket = _pending_ticket(client, db, monkeypatch)
    assert client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers).status_code == 200

    again = client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert again.status_code == 400
    assert db.query(IncomeTransaction).filter_by(reference_id=f"seva_ticket:{ticket['id']}").count() == 1


def test_cannot_collect_payment_on_a_free_ticket(client, db, monkeypatch, staff):
    _, headers = staff
    pooja = Pooja(name="Free Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)

    sent = _capture_email(monkeypatch)
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": "free@example.com"})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": "free@example.com", "code": _code_from(sent)}).json()["booking_token"]
    ticket = client.post("/api/v1/seva-tickets", json={
        "seva_id": pooja.id, "devotee_name": "Ravi", "mobile_number": "9876543213",
        "seva_date": (date.today() + timedelta(days=1)).isoformat(),
        "email": "free@example.com", "booking_token": token,
    }).json()

    r = client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert r.status_code == 400
