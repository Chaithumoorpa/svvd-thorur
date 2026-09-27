"""Occasion blessing emails. A seva booking (Abhishekam included) can say
what it's for - a birthday, a wedding anniversary, ... - and gets a personal
blessing email on its seva date once paid for (or booked, if the seva is
free): sent by the daily cron job, or right away when the booking is paid/
booked on or after that date. Never twice, never more than
GREETING_WINDOW_DAYS late. A donation has no future date, so its blessing
goes out as soon as it's recorded."""
import re
from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.models.pooja import Pooja
from app.models.seva_ticket import SevaTicket, TicketStatus
from app.services.occasion_greeting_service import GREETING_WINDOW_DAYS, OccasionGreetingService

TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)


def _capture_email(monkeypatch, returns=True):
    sent = MagicMock(return_value=returns)
    monkeypatch.setattr("app.services.email_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    for call in reversed(sent.call_args_list):
        match = re.search(r"\b(\d{6})\b", call.args[2])
        if match:
            return match.group(1)
    raise AssertionError("No OTP code found in any sent email")


def _blessing_calls(sent):
    return [c for c in sent.call_args_list if c.args[1].startswith("Blessings on your")]


def _pooja(db, is_paid=False):
    pooja = Pooja(name="Archana", pooja_type="daily", is_paid=is_paid,
                  suggested_amount=300 if is_paid else None, is_active=True)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    return pooja


def _book(client, sent, pooja_id, occasion="Birthday", seva_date=TOMORROW, email="devotee@example.com", **extra):
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": email})
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": email, "code": _code_from(sent)}).json()["booking_token"]
    payload = {
        "seva_id": pooja_id, "devotee_name": "Lakshmi", "mobile_number": "9876543214",
        "seva_date": seva_date.isoformat(), "email": email, "booking_token": token, **extra,
    }
    if occasion is not None:
        payload["occasion"] = occasion
    r = client.post("/api/v1/seva-tickets", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def _ticket(db, ticket_id) -> SevaTicket:
    return db.query(SevaTicket).filter(SevaTicket.id == UUID(ticket_id)).one()


# ------------------------------------------------------------------------ seva


def test_free_seva_for_a_later_date_is_blessed_on_that_date(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    _book(client, sent, _pooja(db).id, occasion="Birthday", seva_date=TOMORROW)
    assert _blessing_calls(sent) == []  # not at booking time

    greetings = OccasionGreetingService(db)
    assert greetings.send_due(TODAY) == 0
    assert greetings.send_due(TOMORROW) == 1
    blessings = _blessing_calls(sent)
    assert len(blessings) == 1
    assert blessings[0].args[0] == "devotee@example.com"
    assert "Birthday" in blessings[0].args[1]

    assert greetings.send_due(TOMORROW) == 0  # idempotent - never twice
    assert len(_blessing_calls(sent)) == 1


def test_free_seva_booked_for_today_is_blessed_immediately(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db).id, seva_date=TODAY)
    assert len(_blessing_calls(sent)) == 1
    assert _ticket(db, ticket["id"]).greeting_sent_at is not None
    assert OccasionGreetingService(db).send_due(TODAY) == 0


def test_free_seva_without_occasion_sends_no_blessing(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    _book(client, sent, _pooja(db).id, occasion=None, seva_date=TODAY)
    assert _blessing_calls(sent) == []
    assert OccasionGreetingService(db).send_due(TODAY) == 0


def test_pending_seva_is_blessed_on_its_date_only_once_paid(client, db, monkeypatch, staff):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db, is_paid=True).id, occasion="Wedding Anniversary")
    assert ticket["payment_status"] == "PENDING"

    greetings = OccasionGreetingService(db)
    assert greetings.send_due(TOMORROW) == 0  # unpaid on the day: nothing

    assert client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers).status_code == 200
    assert _blessing_calls(sent) == []  # paid before the date: wait for it
    assert greetings.send_due(TOMORROW) == 1
    assert "Wedding Anniversary" in _blessing_calls(sent)[0].args[1]


def test_pending_seva_paid_on_its_date_is_blessed_at_collection(client, db, monkeypatch, staff):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db, is_paid=True).id, seva_date=TODAY)
    assert _blessing_calls(sent) == []

    client.post(f"/api/v1/seva-tickets/{ticket['id']}/collect-payment", headers=headers)
    assert len(_blessing_calls(sent)) == 1


def test_cancelled_seva_is_never_blessed(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db).id)
    _ticket(db, ticket["id"]).status = TicketStatus.CANCELLED
    db.commit()
    assert OccasionGreetingService(db).send_due(TOMORROW) == 0


def test_blessing_is_not_sent_once_the_window_has_passed(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db).id)
    greetings = OccasionGreetingService(db)
    last_day = TOMORROW + timedelta(days=GREETING_WINDOW_DAYS - 1)
    assert greetings.send_due(last_day + timedelta(days=1)) == 0  # e.g. cron down all week
    assert greetings.send_due(last_day) == 1  # still inside it: sent late rather than never
    assert _ticket(db, ticket["id"]).greeting_sent_at is not None


def test_failed_send_is_retried_on_the_next_run(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db).id)

    monkeypatch.setattr("app.services.email_service.EmailService.send", MagicMock(return_value=False))
    greetings = OccasionGreetingService(db)
    assert greetings.send_due(TOMORROW) == 0
    assert _ticket(db, ticket["id"]).greeting_sent_at is None  # claim released

    _capture_email(monkeypatch)
    assert greetings.send_due(TOMORROW) == 1


# -------------------------------------------------------------- email content


def test_blessing_email_links_the_devotees_page_and_the_public_page_if_chosen(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    pooja = _pooja(db)
    pooja.public_blessings = True
    db.commit()
    ticket = _book(client, sent, pooja.id, seva_date=TODAY)
    body = _blessing_calls(sent)[0].args[2]
    assert f"/blessing/{ticket['id']}" in body
    assert "/abhishekam/blessings/" not in body  # private by default

    _book(client, sent, pooja.id, seva_date=TODAY, email="public@example.com", mobile_number="9876543215",
          show_publicly=True, photo_url="https://example.com/p.jpg")
    public_body = _blessing_calls(sent)[-1].args[2]
    assert f"/abhishekam/blessings/{TODAY.isoformat()}" in public_body


def test_cron_entry_point_runs_send_due(client, db, monkeypatch):
    from app.cli import send_occasion_greetings

    sent = _capture_email(monkeypatch)
    ticket = _book(client, sent, _pooja(db).id)
    _ticket(db, ticket["id"]).seva_date = TODAY  # its day has come
    db.commit()
    monkeypatch.setattr(send_occasion_greetings, "SessionLocal", lambda: db)
    send_occasion_greetings.main()
    assert _ticket(db, ticket["id"]).greeting_sent_at is not None


# -------------------------------------------------------------------- donation


@pytest.mark.parametrize("donor_email, occasion, expected", [
    ("ramu@example.com", "House Warming", 1),
    (None, "Birthday", 0),             # no donor email: nothing to send to
    ("sita@example.com", None, 0),     # no occasion: no blessing
])
def test_donation_blessing_goes_out_when_recorded(client, admin, monkeypatch, donor_email, occasion, expected):
    _, headers = admin
    sent = _capture_email(monkeypatch)
    donor = client.post("/api/v1/donors/", headers=headers,
                        json={"name": "Ramu", **({"email": donor_email} if donor_email else {})}).json()
    payload = {"donor_id": donor["id"], "amount": 501, **({"occasion": occasion} if occasion else {})}
    r = client.post("/api/v1/donations/", headers=headers, json=payload)
    assert r.status_code == 201, r.text

    blessings = _blessing_calls(sent)
    assert len(blessings) == expected
    if expected:
        assert blessings[0].args[0] == donor_email
        assert occasion in blessings[0].args[1]
