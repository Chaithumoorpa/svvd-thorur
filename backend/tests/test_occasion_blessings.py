"""POST /occasion-blessings (public, OTP-gated) through payment collection to
the private view page. Payment is pay-at-counter, same PENDING/PAID pattern
as a paid seva ticket - the view page reveals nothing beyond the occasion/
reference number until staff collect the Rs 50 fee, and hides everything
again once the 7-day visibility window has passed."""
import re
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID

from app.models.finance import IncomeSourceType, IncomeTransaction
from app.models.occasion_blessing import BLESSING_VISIBILITY_DAYS, BlessingPaymentStatus, OccasionBlessing


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


def _create_blessing(client, sent, email="devotee@example.com", occasion="Birthday", **overrides):
    client.post("/api/v1/occasion-blessings/request-otp", json={"email": email})
    token = client.post("/api/v1/occasion-blessings/verify-otp",
                        json={"email": email, "code": _code_from(sent)}).json()["booking_token"]
    payload = {
        "devotee_name": "Lakshmi", "mobile_number": "9876543214", "email": email,
        "occasion": occasion, "occasion_date": date.today().isoformat(),
        "photo_url": "https://example.com/photo.jpg", "booking_token": token,
        **overrides,
    }
    r = client.post("/api/v1/occasion-blessings", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_blessing_is_pending_with_fixed_fee(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    blessing = _create_blessing(client, sent)
    assert blessing["payment_status"] == "PENDING"
    assert float(blessing["amount"]) == 50.0
    assert blessing["reference_number"].startswith(f"BLESS-{date.today().year}-")

    confirmations = [c for c in sent.call_args_list if "request received" in c.args[1]]
    assert len(confirmations) == 1
    assert confirmations[0].args[0] == "devotee@example.com"
    assert blessing["reference_number"] in confirmations[0].args[2]


def test_view_pending_blessing_reveals_nothing_but_occasion(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    blessing = _create_blessing(client, sent, occasion="Wedding Anniversary")

    r = client.get(f"/api/v1/occasion-blessings/{blessing['id']}/view")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["occasion"] == "Wedding Anniversary"
    assert body["reference_number"] == blessing["reference_number"]
    assert body["photo_url"] is None
    assert body["devotee_name"] is None
    assert body["message"] is None


def test_collect_payment_activates_the_page(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    blessing = _create_blessing(client, sent)

    r = client.post(f"/api/v1/occasion-blessings/{blessing['id']}/collect-payment", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["payment_status"] == "PAID"

    view = client.get(f"/api/v1/occasion-blessings/{blessing['id']}/view").json()
    assert view["status"] == "active"
    assert view["photo_url"] == "https://example.com/photo.jpg"
    assert view["devotee_name"] == "Lakshmi"
    assert view["expires_at"] is not None

    ready_emails = [c for c in sent.call_args_list if "page is ready" in c.args[1]]
    assert len(ready_emails) == 1


def test_collect_payment_posts_income_and_cannot_repeat(client, staff, db, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    blessing = _create_blessing(client, sent)

    client.post(f"/api/v1/occasion-blessings/{blessing['id']}/collect-payment", headers=headers)
    income = db.query(IncomeTransaction).filter(
        IncomeTransaction.reference_id == f"occasion_blessing:{blessing['id']}"
    ).one()
    assert income.source_type == IncomeSourceType.OCCASION_BLESSING
    assert float(income.amount) == 50.0

    again = client.post(f"/api/v1/occasion-blessings/{blessing['id']}/collect-payment", headers=headers)
    assert again.status_code == 400


def test_collect_payment_requires_permission(client, trustee, monkeypatch):
    _, headers = trustee
    sent = _capture_email(monkeypatch)
    blessing = _create_blessing(client, sent)
    r = client.post(f"/api/v1/occasion-blessings/{blessing['id']}/collect-payment", headers=headers)
    assert r.status_code == 403


def test_view_expires_after_seven_days(client, staff, db, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    blessing = _create_blessing(client, sent)
    client.post(f"/api/v1/occasion-blessings/{blessing['id']}/collect-payment", headers=headers)

    row = db.query(OccasionBlessing).filter(OccasionBlessing.id == UUID(blessing["id"])).one()
    row.paid_at = datetime.now() - timedelta(days=BLESSING_VISIBILITY_DAYS, hours=1)
    db.commit()

    view = client.get(f"/api/v1/occasion-blessings/{blessing['id']}/view").json()
    assert view["status"] == "expired"
    assert view["photo_url"] is None
    assert view["devotee_name"] is None


def test_view_unknown_id_is_404(client):
    assert client.get("/api/v1/occasion-blessings/00000000-0000-0000-0000-000000000000/view").status_code == 404


def test_create_requires_all_mandatory_fields(client, monkeypatch):
    sent = _capture_email(monkeypatch)
    client.post("/api/v1/occasion-blessings/request-otp", json={"email": "a@example.com"})
    token = client.post("/api/v1/occasion-blessings/verify-otp",
                        json={"email": "a@example.com", "code": _code_from(sent)}).json()["booking_token"]
    base = {
        "devotee_name": "Ravi", "mobile_number": "9876543210", "email": "a@example.com",
        "occasion": "Birthday", "occasion_date": date.today().isoformat(),
        "photo_url": "https://example.com/photo.jpg", "booking_token": token,
    }
    for missing in ("devotee_name", "mobile_number", "occasion", "occasion_date", "photo_url"):
        payload = {k: v for k, v in base.items() if k != missing}
        assert client.post("/api/v1/occasion-blessings", json=payload).status_code == 422, missing


def test_admin_list_shows_pending_and_paid(client, staff, monkeypatch):
    _, headers = staff
    sent = _capture_email(monkeypatch)
    a = _create_blessing(client, sent, email="a@example.com")
    b = _create_blessing(client, sent, email="b@example.com")
    client.post(f"/api/v1/occasion-blessings/{a['id']}/collect-payment", headers=headers)

    everyone = client.get("/api/v1/occasion-blessings", headers=headers).json()
    assert {x["id"] for x in everyone} == {a["id"], b["id"]}

    pending_only = client.get("/api/v1/occasion-blessings?pending_only=true", headers=headers).json()
    assert {x["id"] for x in pending_only} == {b["id"]}


def test_upload_url_is_public_but_inert_without_s3(client):
    r = client.post("/api/v1/occasion-blessings/upload-url", json={"content_type": "image/jpeg"})
    assert r.status_code == 503  # S3 not configured in tests
