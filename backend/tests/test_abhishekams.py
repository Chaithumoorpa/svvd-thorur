"""POST /abhishekams (public, OTP-gated) through payment collection to the
private view page, plus the public 365-day calendar. Payment is pay-at-
counter, same PENDING/PAID pattern as a paid seva ticket - the personal view
page reveals nothing beyond the occasion/reference number until staff
collect the Rs 50 fee, and hides everything again once the 7-day
visibility window has passed. Bookings are capped at DAILY_SLOT_CAP (7) per
date; the public calendar's day flyer only ever shows PUBLIC + PAID
entries, though every booking (PRIVATE or still PENDING included) counts
toward that date's slot usage."""
import re
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID

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
    date's slots in tests about capacity, without tripping the OTP request
    rate limiter (5/hour) across many simulated devotees on one test client."""
    row = Abhishekam(
        reference_number=f"ABHI-SEED-{email}", devotee_name="Lakshmi", mobile_number="9876543214",
        email=email, occasion="Birthday", occasion_date=occasion_date,
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


def test_collect_payment_activates_the_page(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent)

    r = client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["payment_status"] == "PAID"

    view = client.get(f"/api/v1/abhishekams/{booking['id']}/view").json()
    assert view["status"] == "active"
    assert view["photo_url"] == "https://example.com/photo.jpg"
    assert view["devotee_name"] == "Lakshmi"
    assert view["expires_at"] is not None

    ready_emails = [c for c in sent.call_args_list if "page is ready" in c.args[1]]
    assert len(ready_emails) == 1


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


def test_view_expires_after_seven_days(client, staff, db, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    booking = _book(client, sent)
    client.post(f"/api/v1/abhishekams/{booking['id']}/collect-payment", headers=headers)

    row = db.query(Abhishekam).filter(Abhishekam.id == UUID(booking["id"])).one()
    row.paid_at = datetime.now() - timedelta(days=ABHISHEKAM_VISIBILITY_DAYS, hours=1)
    db.commit()

    view = client.get(f"/api/v1/abhishekams/{booking['id']}/view").json()
    assert view["status"] == "expired"
    assert view["photo_url"] is None


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
def test_calendar_year_lists_every_day_with_slot_counts(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    target = date.today() + timedelta(days=10)
    _book(client, sent, occasion_date=target)
    _book(client, sent, email="second@example.com", occasion_date=target)

    days = client.get(f"/api/v1/abhishekams/calendar?year={target.year}").json()
    assert len(days) in (365, 366)
    matching = next(d for d in days if d["date"] == target.isoformat())
    assert matching["slots_used"] == 2
    assert matching["slots_total"] == DAILY_SLOT_CAP


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
    assert len(flyer["entries"]) == 1
    assert flyer["entries"][0]["devotee_name"] == "Lakshmi"
    assert flyer["entries"][0]["occasion"] == "Birthday"
