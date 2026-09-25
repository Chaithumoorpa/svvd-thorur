"""A devotee (seva booking) or donor (donation) can optionally say what a
paid transaction is for - a birthday, a wedding anniversary, ... - and gets
a personal blessing email once it's actually paid: immediately for a FREE
seva or a donation (already "paid" the moment it's recorded), or once the
fee is collected at the counter for a PENDING (pay-at-counter) seva."""
import re
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.models.pooja import Pooja


def _capture_email(monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.email_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    for call in sent.call_args_list:
        match = re.search(r"\b(\d{6})\b", call.args[2])
        if match:
            return match.group(1)
    raise AssertionError("No OTP code found in any sent email")


def _blessing_calls(sent):
    return [c for c in sent.call_args_list if c.args[1].startswith("Blessings on your")]


def _book(client, sent, pooja_id, occasion=None, email="devotee@example.com"):
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": email})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": email, "code": _code_from(sent)}).json()["booking_token"]
    payload = {
        "seva_id": pooja_id, "devotee_name": "Lakshmi", "mobile_number": "9876543214",
        "seva_date": (date.today() + timedelta(days=1)).isoformat(),
        "email": email, "booking_token": token,
    }
    if occasion is not None:
        payload["occasion"] = occasion
    r = client.post("/api/v1/seva-tickets", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_free_seva_with_occasion_sends_blessing_immediately(client, db, monkeypatch):
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    sent = _capture_email(monkeypatch)

    ticket = _book(client, sent, pooja.id, occasion="Birthday")
    assert ticket["occasion"] == "Birthday"

    blessings = _blessing_calls(sent)
    assert len(blessings) == 1
    assert blessings[0].args[0] == "devotee@example.com"
    assert "Birthday" in blessings[0].args[1]


def test_free_seva_without_occasion_sends_no_blessing(client, db, monkeypatch):
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    sent = _capture_email(monkeypatch)

    _book(client, sent, pooja.id)
    assert _blessing_calls(sent) == []


def test_pending_seva_defers_blessing_until_payment_collected(client, db, monkeypatch, staff):
    _, headers = staff
    pooja = Pooja(name="Abhishekam", pooja_type="special", is_paid=True, suggested_amount=300, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    sent = _capture_email(monkeypatch)

    ticket = _book(client, sent, pooja.id, occasion="Wedding Anniversary")
    assert ticket["payment_status"] == "PENDING"
    assert _blessing_calls(sent) == []  # not paid yet

    collected = client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert collected.status_code == 200

    blessings = _blessing_calls(sent)
    assert len(blessings) == 1
    assert "Wedding Anniversary" in blessings[0].args[1]


def test_donation_with_occasion_emails_the_donor(client, admin, monkeypatch):
    _, headers = admin
    sent = _capture_email(monkeypatch)
    donor = client.post("/api/v1/donors/", headers=headers,
                        json={"name": "Ramu", "email": "ramu@example.com"}).json()

    r = client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": 501, "occasion": "House Warming"})
    assert r.status_code == 201, r.text
    assert r.json()["occasion"] == "House Warming"

    blessings = _blessing_calls(sent)
    assert len(blessings) == 1
    assert blessings[0].args[0] == "ramu@example.com"
    assert "House Warming" in blessings[0].args[1]


def test_donation_with_occasion_but_no_donor_email_sends_nothing(client, admin, monkeypatch):
    _, headers = admin
    sent = _capture_email(monkeypatch)
    donor = client.post("/api/v1/donors/", headers=headers, json={"name": "No Email Donor"}).json()

    r = client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": 100, "occasion": "Birthday"})
    assert r.status_code == 201, r.text
    assert _blessing_calls(sent) == []


def test_donation_without_occasion_sends_no_blessing(client, admin, monkeypatch):
    _, headers = admin
    sent = _capture_email(monkeypatch)
    donor = client.post("/api/v1/donors/", headers=headers,
                        json={"name": "Sita", "email": "sita@example.com"}).json()

    r = client.post("/api/v1/donations/", headers=headers, json={"donor_id": donor["id"], "amount": 100})
    assert r.status_code == 201, r.text
    assert _blessing_calls(sent) == []
