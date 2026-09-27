"""Abhishekam as an ordinary seva: a seva can cap its bookings per date
(daily_slot_cap - online and counter alike, cancelled tickets free their
slot) and offer public blessings (public_blessings): the devotee may add one
occasion photo and choose to show name + occasion publicly - on the seva's
calendar pop-ups for good, and with the photo on that day's blessings page
for BLESSING_VISIBLE_DAYS. Each booking made for an occasion also gets its
own blessing page, linked from the greeting email."""
import re
from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.models.pooja import Pooja
from app.models.seva_ticket import PaymentStatus, SevaTicket, TicketStatus
from app.services.blessing_service import BLESSING_VISIBLE_DAYS

TODAY = date.today()
SOON = TODAY + timedelta(days=10)


@pytest.fixture()
def sent(monkeypatch):
    mock = MagicMock(return_value=True)
    monkeypatch.setattr("app.services.email_service.EmailService.send", mock)
    return mock


def _seva(db, cap=7, blessings=True, name="Abhishekam"):
    pooja = Pooja(name=name, pooja_type="daily", is_paid=True, suggested_amount=700,
                  daily_slot_cap=cap, public_blessings=blessings)
    db.add(pooja)
    db.commit()
    db.refresh(pooja)
    return pooja


_n = {"i": 0}


def _ticket(db, seva, day, payment=PaymentStatus.PAID, status=TicketStatus.ACTIVE, **fields):
    """A ticket straight into the database - filling a date's slots without the
    OTP flow (whose request limiter allows 5 an hour per test client)."""
    _n["i"] += 1
    ticket = SevaTicket(ticket_number=f"T-{_n['i']}", seva_id=seva.id, seva_name=seva.name, devotee_name="Lakshmi",
                        mobile_number=f"98765{_n['i']:05d}", seva_date=day, payment_status=payment, amount=700,
                        status=status, qr_token=f"qr-{_n['i']}", **fields)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _book_online(client, sent, seva, day=SOON, email="devotee@example.com", **extra):
    client.post("/api/v1/seva-tickets/booking/request-otp", json={"email": email})
    code = next(re.search(r"\b(\d{6})\b", c.args[2]).group(1) for c in reversed(sent.call_args_list)
                if re.search(r"\b(\d{6})\b", c.args[2]))
    token = client.post("/api/v1/seva-tickets/booking/verify-otp",
                        json={"email": email, "code": code}).json()["booking_token"]
    return client.post("/api/v1/seva-tickets", json={
        "seva_id": seva.id, "devotee_name": "Chaithanya", "mobile_number": "9876543210",
        "seva_date": day.isoformat(), "email": email, "booking_token": token, **extra,
    })


# ------------------------------------------------------------------ seva settings


def test_admin_sets_and_clears_slots_per_day_and_public_blessings(client, admin):
    _, headers = admin
    created = client.post("/api/v1/poojas", headers=headers, json={
        "name": "Abhishekam", "is_paid": True, "suggested_amount": 700,
        "daily_slot_cap": 7, "public_blessings": True,
    }).json()
    assert (created["daily_slot_cap"], created["public_blessings"]) == (7, True)

    updated = client.put(f"/api/v1/poojas/{created['id']}", headers=headers, json={"daily_slot_cap": None}).json()
    assert (updated["daily_slot_cap"], updated["public_blessings"]) == (None, True)  # unlimited; flag untouched


# ------------------------------------------------------------------ slots per day


def test_booking_the_eighth_slot_is_refused_online(client, db, sent):
    seva = _seva(db)
    for i in range(7):
        _ticket(db, seva, SOON, payment=PaymentStatus.PENDING if i % 2 else PaymentStatus.PAID)
    r = _book_online(client, sent, seva)
    assert r.status_code == 409
    assert "fully booked" in r.json()["detail"]


def test_a_cancelled_ticket_frees_its_slot(client, db, sent):
    seva = _seva(db)
    for _ in range(6):
        _ticket(db, seva, SOON)
    _ticket(db, seva, SOON, status=TicketStatus.CANCELLED)
    assert _book_online(client, sent, seva).status_code == 200


def test_counter_tickets_count_toward_and_respect_the_cap(client, db, staff):
    _, headers = staff
    seva = _seva(db, cap=2)
    _ticket(db, seva, SOON)
    counter = {"seva_id": seva.id, "devotee_name": "Ravi", "mobile_number": "9876543211", "seva_date": SOON.isoformat()}
    assert client.post("/api/v1/seva-tickets/admin", headers=headers, json=counter).status_code == 200
    assert client.post("/api/v1/seva-tickets/admin", headers=headers,
                       json={**counter, "mobile_number": "9876543212"}).status_code == 409


def test_a_seva_without_a_cap_takes_any_number(client, db, sent):
    seva = _seva(db, cap=None)
    for _ in range(12):
        _ticket(db, seva, SOON)
    assert _book_online(client, sent, seva).status_code == 200


# ---------------------------------------------------------------- public blessing


def test_blessing_photo_and_public_choice_are_saved(client, db, sent):
    seva = _seva(db)
    r = _book_online(client, sent, seva, occasion="Birthday", photo_url="https://example.com/p.jpg",
                     show_publicly=True)
    assert r.status_code == 200, r.text
    assert (r.json()["photo_url"], r.json()["show_publicly"]) == ("https://example.com/p.jpg", True)


def test_public_blessing_needs_a_seva_that_offers_it(client, db, sent):
    seva = _seva(db, blessings=False, name="Archana")
    r = _book_online(client, sent, seva, occasion="Birthday", show_publicly=True)
    assert r.status_code == 400
    assert "public blessings" in r.json()["detail"]


def test_public_blessing_needs_an_occasion(client, db, sent):
    r = _book_online(client, sent, _seva(db), show_publicly=True)
    assert r.status_code == 422


def test_private_is_the_default(client, db, sent):
    r = _book_online(client, sent, _seva(db), occasion="Birthday")
    assert r.json()["show_publicly"] is False


# ------------------------------------------------------------------------ calendar


def test_calendar_counts_every_ticket_holding_a_slot(client, db):
    seva = _seva(db)
    _ticket(db, seva, SOON)
    _ticket(db, seva, SOON, payment=PaymentStatus.PENDING)
    _ticket(db, seva, SOON, status=TicketStatus.CANCELLED)
    start, end = TODAY - timedelta(days=182), TODAY + timedelta(days=182)
    days = client.get(f"/api/v1/poojas/{seva.id}/calendar?start={start}&end={end}").json()
    assert len(days) == 365
    day = next(d for d in days if d["date"] == SOON.isoformat())
    assert (day["slots_used"], day["slots_total"]) == (2, 7)


def test_calendar_rejects_bad_ranges_and_unknown_sevas(client, db):
    seva = _seva(db)
    assert client.get(f"/api/v1/poojas/{seva.id}/calendar?start={TODAY}&end={TODAY - timedelta(days=1)}").status_code == 400
    assert client.get(f"/api/v1/poojas/{seva.id}/calendar?start={TODAY}&end={TODAY + timedelta(days=400)}").status_code == 400
    assert client.get(f"/api/v1/poojas/9999/calendar?start={TODAY}&end={TODAY}").status_code == 404


def test_day_shows_only_public_settled_bookings_with_photos_while_active(client, db):
    seva = _seva(db)
    public = {"occasion": "Birthday", "show_publicly": True, "photo_url": "https://example.com/p.jpg"}
    _ticket(db, seva, TODAY, **public)
    _ticket(db, seva, TODAY, payment=PaymentStatus.PENDING, **public)       # not paid yet
    _ticket(db, seva, TODAY, occasion="Birthday", photo_url="https://example.com/q.jpg")  # private
    _ticket(db, seva, TODAY, status=TicketStatus.CANCELLED, **public)

    day = client.get(f"/api/v1/poojas/{seva.id}/calendar/{TODAY}").json()
    assert day["slots_used"] == 3
    assert day["blessing_status"] == "active"
    assert day["entries"] == [{"devotee_name": "Lakshmi", "occasion": "Birthday",
                               "photo_url": "https://example.com/p.jpg"}]


@pytest.mark.parametrize("days_from_today, status", [(3, "upcoming"), (-BLESSING_VISIBLE_DAYS, "archived")])
def test_day_keeps_names_but_not_photos_outside_the_window(client, db, days_from_today, status):
    seva = _seva(db)
    day = TODAY + timedelta(days=days_from_today)
    _ticket(db, seva, day, occasion="Birthday", show_publicly=True, photo_url="https://example.com/p.jpg")
    body = client.get(f"/api/v1/poojas/{seva.id}/calendar/{day}").json()
    assert body["blessing_status"] == status
    assert body["entries"] == [{"devotee_name": "Lakshmi", "occasion": "Birthday", "photo_url": None}]


# ------------------------------------------------------------ personal blessing page


@pytest.mark.parametrize("days_from_today, payment, status", [
    (0, PaymentStatus.PENDING, "pending"),
    (5, PaymentStatus.PAID, "scheduled"),
    (0, PaymentStatus.PAID, "active"),
    (-(BLESSING_VISIBLE_DAYS - 1), PaymentStatus.PAID, "active"),  # its last day
    (-BLESSING_VISIBLE_DAYS, PaymentStatus.PAID, "expired"),
])
def test_personal_blessing_page_states(client, db, days_from_today, payment, status):
    ticket = _ticket(db, _seva(db), TODAY + timedelta(days=days_from_today), payment=payment,
                     occasion="Birthday", photo_url="https://example.com/p.jpg")
    body = client.get(f"/api/v1/seva-tickets/{ticket.id}/blessing").json()
    assert body["status"] == status
    assert body["occasion"] == "Birthday"
    shown = status == "active"
    assert (body["devotee_name"] is not None, body["photo_url"] is not None) == (shown, shown)


def test_no_blessing_page_without_an_occasion(client, db):
    ticket = _ticket(db, _seva(db), TODAY)
    assert client.get(f"/api/v1/seva-tickets/{ticket.id}/blessing").status_code == 404


# ------------------------------------------------------------------ counter tickets


def test_counter_ticket_keeps_occasion_and_email_and_greets_on_the_day(client, db, staff, sent):
    _, headers = staff
    seva = _seva(db)
    r = client.post("/api/v1/seva-tickets/admin", headers=headers, json={
        "seva_id": seva.id, "devotee_name": "Ravi", "mobile_number": "9876543211", "seva_date": TODAY.isoformat(),
        "occasion": "Wedding Anniversary", "email": "ravi@example.com", "payment_status": "PAID", "amount": 700,
    })
    assert r.status_code == 200, r.text
    assert r.json()["occasion"] == "Wedding Anniversary"
    ticket = db.query(SevaTicket).filter(SevaTicket.id == UUID(r.json()["id"])).one()
    assert ticket.email == "ravi@example.com"
    blessings = [c for c in sent.call_args_list if c.args[1] == "Blessings on your Wedding Anniversary"]
    assert [c.args[0] for c in blessings] == ["ravi@example.com"]


def test_blessing_photo_upload_is_public_but_inert_without_s3(client):
    r = client.post("/api/v1/seva-tickets/booking/upload-url", json={"content_type": "image/jpeg"})
    assert r.status_code == 503  # S3 not configured in tests
