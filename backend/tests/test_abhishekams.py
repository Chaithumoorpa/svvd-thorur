"""POST /abhishekams (public, OTP-gated) through payment collection to the
private view page, plus the public rolling calendar. Payment is pay-at-
counter, same PENDING/PAID pattern as a paid seva ticket - the personal view
page reveals nothing beyond the occasion/reference number until the fee is
paid AND occasion_date has arrived, then shows everything for 7 days.
Bookings are capped at DAILY_SLOT_CAP (7) per date; the public calendar only
ever shows PUBLIC + PAID entries (photos only during that 7-day window),
though every booking (PRIVATE or still PENDING included) counts toward that
date's slot usage."""
import re
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.models.abhishekam import Abhishekam, AbhishekamPaymentStatus, ABHISHEKAM_VISIBILITY_DAYS, DAILY_SLOT_CAP
from app.models.finance import IncomeSourceType, IncomeTransaction


def _capture_email(monkeypatch):
    sent = MagicMock()
    monkeypatch.setattr("app.services.email_service.EmailService.send", sent)
    return sent


def _code_from(sent) -> str:
    for call in reversed(sent.call_args_list):  # most recent OTP request first
        match = re.search(r"\b(\d{6})\b", call.args[2])
        if match:
            return match.group(1)
    raise AssertionError("No OTP code found")


def _seed(db, occasion_date, email, visibility="PRIVATE", payment_status=AbhishekamPaymentStatus.PENDING):
    """Inserts a booking directly, bypassing OTP/HTTP - for quickly filling a
    date's slots without tripping the OTP request rate limiter (5/hour) across
    many simulated devotees on one test client, or for a date in the past
    (which the public booking form rightly refuses)."""
    row = Abhishekam(
        reference_number=f"ABHI-SEED-{email}", devotee_name="Lakshmi", mobile_number="9876543214",
        email=email, occasion="Birthday", occasion_date=occasion_date, relation="My daughter",
        photo_url="https://example.com/photo.jpg", visibility=visibility,
        amount=50, payment_status=payment_status,
    )
    db.add(row)
    db.commit()
    return row


def _book(client, sent, email="devotee@example.com", occasion="Birthday",
          occasion_date=None, **overrides):
    client.post("/api/v1/abhishekams/request-otp", json={"email": email})
    token = client.post("/api/v1/abhishekams/verify-otp",
                        json={"email": email, "code": _code_from(sent)}).json()["booking_token"]
    payload = {
        "devotee_name": "Lakshmi", "mobile_number": "9876543214", "email": email,
        "occasion": occasion, "occasion_date": (occasion_date or date.today()).isoformat(),
        "photo_url": "https://example.com/photo.jpg", "booking_token": token,
        **overrides,
    }
    r = client.post("/api/v1/abhishekams", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def test_booking_is_pending_private_by_default_with_fixed_fee(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent)
    assert booking["payment_status"] == "PENDING"
    assert booking["visibility"] == "PRIVATE"
    assert float(booking["amount"]) == 50.0
    assert booking["reference_number"].startswith(f"ABHI-{date.today().year}-")

    confirmations = [c for c in sent.call_args_list if "booking received" in c.args[1]]
    assert len(confirmations) == 1
    assert confirmations[0].args[0] == "devotee@example.com"
    assert booking["reference_number"] in confirmations[0].args[2]


def test_view_pending_booking_reveals_nothing_but_occasion(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent, occasion="Wedding Anniversary")

    r = client.get(f"/api/v1/abhishekams/{booking['id']}/view")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["occasion"] == "Wedding Anniversary"
    assert body["reference_number"] == booking["reference_number"]
    assert body["photo_url"] is None
    assert body["devotee_name"] is None


def test_payment_on_the_day_opens_the_page_and_sends_the_blessing(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent)  # for today

    r = client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["payment_status"] == "PAID"
    assert r.json()["greeting_sent_at"] is not None

    view = client.get(f"/api/v1/abhishekams/{booking['id']}/view").json()
    assert view["status"] == "active"
    assert view["photo_url"] == "https://example.com/photo.jpg"
    assert view["devotee_name"] == "Lakshmi"
    assert view["visible_until"] == (date.today() + timedelta(days=ABHISHEKAM_VISIBILITY_DAYS - 1)).isoformat()

    blessings = [c for c in sent.call_args_list if c.args[1] == "Blessings on your Birthday"]
    assert len(blessings) == 1
    assert f"/abhishekam/{booking['id']}" in blessings[0].args[2]


def test_payment_before_the_date_schedules_the_page_and_blessing(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent, occasion_date=date.today() + timedelta(days=10))

    paid = client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers).json()
    assert paid["greeting_sent_at"] is None

    view = client.get(f"/api/v1/abhishekams/{booking['id']}/view").json()
    assert view["status"] == "scheduled"
    assert view["photo_url"] is None

    subjects = [c.args[1] for c in sent.call_args_list]
    assert f"Payment received: {booking['reference_number']}" in subjects
    assert not any(s.startswith("Blessings on your") for s in subjects)


def test_collect_payment_posts_income_and_cannot_repeat(client, staff, db, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent)

    client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers)
    income = db.query(IncomeTransaction).filter(
        IncomeTransaction.reference_id == f"abhishekam:{booking['id']}"
    ).one()
    assert income.source_type == IncomeSourceType.ABHISHEKAM
    assert float(income.amount) == 50.0

    again = client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers)
    assert again.status_code == 400


def test_collect_payment_requires_permission(client, trustee, monkeypatch):
    _, headers = trustee
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent)
    r = client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers)
    assert r.status_code == 403


def test_view_stays_up_for_seven_days_from_the_occasion_date(client, db):
    last_day = _seed(db, date.today() - timedelta(days=ABHISHEKAM_VISIBILITY_DAYS - 1), "last@example.com",
                     payment_status=AbhishekamPaymentStatus.PAID)
    gone = _seed(db, date.today() - timedelta(days=ABHISHEKAM_VISIBILITY_DAYS), "gone@example.com",
                 payment_status=AbhishekamPaymentStatus.PAID)

    view = client.get(f"/api/v1/abhishekams/{last_day.id}/view").json()
    assert view["status"] == "active"
    assert view["visible_until"] == date.today().isoformat()

    view = client.get(f"/api/v1/abhishekams/{gone.id}/view").json()
    assert view["status"] == "expired"
    assert view["photo_url"] is None


def test_booking_a_past_date_is_rejected(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    client.post("/api/v1/abhishekams/request-otp", json={"email": "late@example.com"})
    token = client.post("/api/v1/abhishekams/verify-otp",
                        json={"email": "late@example.com", "code": _code_from(sent)}).json()["booking_token"]
    r = client.post("/api/v1/abhishekams", json={
        "devotee_name": "Late", "mobile_number": "9876543210", "email": "late@example.com",
        "occasion": "Birthday", "occasion_date": (date.today() - timedelta(days=1)).isoformat(),
        "photo_url": "https://example.com/photo.jpg", "booking_token": token,
    })
    assert r.status_code == 422
    assert "past" in r.text


def test_view_unknown_id_is_404(client):
    assert client.get("/api/v1/abhishekams/00000000-0000-0000-0000-000000000000/view").status_code == 404


def test_create_requires_all_mandatory_fields(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    client.post("/api/v1/abhishekams/request-otp", json={"email": "a@example.com"})
    token = client.post("/api/v1/abhishekams/verify-otp",
                        json={"email": "a@example.com", "code": _code_from(sent)}).json()["booking_token"]
    base = {
        "devotee_name": "Ravi", "mobile_number": "9876543210", "email": "a@example.com",
        "occasion": "Birthday", "occasion_date": date.today().isoformat(),
        "photo_url": "https://example.com/photo.jpg", "booking_token": token,
    }
    for missing in ("devotee_name", "mobile_number", "occasion", "occasion_date", "photo_url"):
        payload = {k: v for k, v in base.items() if k != missing}
        assert client.post("/api/v1/abhishekams", json=payload).status_code == 422, missing


def test_admin_list_shows_pending_and_paid(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    a = _book(client, sent, email="a@example.com")
    b = _book(client, sent, email="b@example.com")
    client.post(f"/api/v1/abhishekams/{a['id']}/collect-payment", headers=headers)

    everyone = client.get("/api/v1/abhishekams", headers=headers).json()
    assert {x["id"] for x in everyone} == {a["id"], b["id"]}

    pending_only = client.get("/api/v1/abhishekams?pending_only=true", headers=headers).json()
    assert {x["id"] for x in pending_only} == {b["id"]}


def test_upload_url_is_public_but_inert_without_s3(client):
    r = client.post("/api/v1/abhishekams/upload-url", json={"content_type": "image/jpeg"})
    assert r.status_code == 503  # S3 not configured in tests


# ----------------------------------------------------------------- daily slot cap
def test_eighth_booking_on_the_same_date_is_rejected(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    target = date.today() + timedelta(days=30)
    for i in range(DAILY_SLOT_CAP):
        _seed(db, target, f"devotee{i}@example.com")

    client.post("/api/v1/abhishekams/request-otp", json={"email": "overflow@example.com"})
    token = client.post("/api/v1/abhishekams/verify-otp",
                        json={"email": "overflow@example.com", "code": _code_from(sent)}).json()["booking_token"]
    r = client.post("/api/v1/abhishekams", json={
        "devotee_name": "Overflow", "mobile_number": "9876543215", "email": "overflow@example.com",
        "occasion": "Birthday", "occasion_date": target.isoformat(),
        "photo_url": "https://example.com/photo.jpg", "booking_token": token,
    })
    assert r.status_code == 409
    assert "fully booked" in r.json()["detail"].lower()


def test_a_pending_booking_still_holds_its_slot(client, db, monkeypatch):
    """Capacity is checked against PENDING + PAID, not just PAID - otherwise
    more than DAILY_SLOT_CAP people could all be told "you're in" before any
    of them actually pays."""
    target = date.today() + timedelta(days=31)
    for i in range(DAILY_SLOT_CAP):
        _seed(db, target, f"holder{i}@example.com")

    remaining = db.query(Abhishekam).filter(
        Abhishekam.occasion_date == target, Abhishekam.payment_status == AbhishekamPaymentStatus.PENDING,
    ).count()
    assert remaining == DAILY_SLOT_CAP


# ----------------------------------------------------------------- public calendar
def test_calendar_lists_every_day_of_the_rolling_window_with_slot_counts(client, db, monkeypatch):
    sent = _capture_email(monkeypatch)
    target = date.today() + timedelta(days=10)
    _book(client, sent, occasion_date=target)
    _book(client, sent, email="second@example.com", occasion_date=target)
    past = _seed(db, date.today() - timedelta(days=100), "past@example.com")

    start, end = date.today() - timedelta(days=182), date.today() + timedelta(days=182)
    days = client.get(f"/api/v1/abhishekams/calendar?start={start}&end={end}").json()
    assert len(days) == 365
    assert days[0]["date"] == start.isoformat() and days[-1]["date"] == end.isoformat()
    by_date = {d["date"]: d for d in days}
    assert by_date[target.isoformat()]["slots_used"] == 2
    assert by_date[target.isoformat()]["slots_total"] == DAILY_SLOT_CAP
    assert by_date[past.occasion_date.isoformat()]["slots_used"] == 1


def test_calendar_rejects_backwards_or_oversized_ranges(client):
    today = date.today()
    assert client.get(f"/api/v1/abhishekams/calendar?start={today}&end={today - timedelta(days=1)}").status_code == 400
    assert client.get(f"/api/v1/abhishekams/calendar?start={today}&end={today + timedelta(days=400)}").status_code == 400
    assert client.get(f"/api/v1/abhishekams/calendar?start={today}&end={today}").status_code == 200


def test_day_flyer_only_shows_public_paid_entries(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    target = date.today() + timedelta(days=20)

    public_paid = _book(client, sent, email="public@example.com", occasion_date=target, visibility="PUBLIC")
    client.post(f"/api/v1/abhishekams/{public_paid['id']}/collect-payment", headers=headers)

    _book(client, sent, email="public_unpaid@example.com", occasion_date=target, visibility="PUBLIC")

    private_paid = _book(client, sent, email="private@example.com", occasion_date=target, visibility="PRIVATE")
    client.post(f"/api/v1/abhishekams/{private_paid['id']}/collect-payment", headers=headers)

    flyer = client.get(f"/api/v1/abhishekams/calendar/{target.isoformat()}").json()
    assert flyer["slots_used"] == 3  # all three still hold a slot
    assert flyer["slots_total"] == DAILY_SLOT_CAP
    assert flyer["blessing_status"] == "upcoming"
    assert flyer["entries"] == [
        # the permanent public timeline: name + occasion, no photo before the day
        {"devotee_name": "Lakshmi", "occasion": "Birthday", "relation": None, "photo_url": None},
    ]


def test_day_photos_are_public_only_for_seven_days_from_the_date(client, db):
    def seed_public_paid(day, email):
        _seed(db, day, email, visibility="PUBLIC", payment_status=AbhishekamPaymentStatus.PAID)

    today = date.today()
    archived_day = today - timedelta(days=ABHISHEKAM_VISIBILITY_DAYS)
    seed_public_paid(today, "today@example.com")
    seed_public_paid(archived_day, "old@example.com")

    active = client.get(f"/api/v1/abhishekams/calendar/{today}").json()
    assert active["blessing_status"] == "active"
    assert active["visible_until"] == (today + timedelta(days=ABHISHEKAM_VISIBILITY_DAYS - 1)).isoformat()
    assert active["entries"][0]["photo_url"] == "https://example.com/photo.jpg"
    assert active["entries"][0]["relation"] == "My daughter"

    archived = client.get(f"/api/v1/abhishekams/calendar/{archived_day}").json()
    assert archived["blessing_status"] == "archived"
    assert archived["entries"] == [
        {"devotee_name": "Lakshmi", "occasion": "Birthday", "relation": None, "photo_url": None},
    ]
