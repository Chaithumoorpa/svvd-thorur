"""The public API must never expose private, draft or inactive data."""
from datetime import date, timedelta

from app.models.announcement import Announcement
from app.models.donor import Donor
from app.models.member import Member
from app.models.pooja import Pooja
from app.services.otp_service import OtpService


def _verified_email(db, email: str) -> tuple:
    """(email, booking_token) for a freshly OTP-verified email, bypassing the
    actual email send (SES isn't configured in tests) by driving the service
    directly - same pattern used for password-reset tokens elsewhere."""
    service = OtpService(db)
    code = service.request_otp(email)
    return email, service.verify_otp(email, code)


def test_announcements_only_published(client, db):
    today = date.today()
    db.add_all([
        Announcement(title="Live", is_active=True),
        Announcement(title="Draft", is_active=False),
        Announcement(title="Expired", is_active=True, end_date=today - timedelta(days=1)),
        Announcement(title="Future", is_active=True, start_date=today + timedelta(days=3)),
        Announcement(title="Window", is_active=True, start_date=today - timedelta(days=1),
                     end_date=today + timedelta(days=1)),
    ])
    db.commit()
    titles = {a["title"] for a in client.get("/api/v1/announcements/").json()}
    assert titles == {"Live", "Window"}
    # the old public switch no longer reveals unpublished items
    titles = {a["title"] for a in client.get("/api/v1/announcements/?show_all=true").json()}
    assert titles == {"Live", "Window"}
    draft = db.query(Announcement).filter_by(title="Draft").one()
    assert client.get(f"/api/v1/announcements/{draft.id}").status_code == 404


def test_committee_endpoint_hides_private_fields(client, db):
    db.add_all([
        Member(name="Shown Trustee", phone="9999999999", email="t@example.com", position="Trustee",
               show_on_website=True, sort_order=1),
        Member(name="Hidden Member", phone="8888888888", show_on_website=False),
        Member(name="Inactive Member", phone="7777777777", show_on_website=True, is_active=False),
    ])
    db.commit()
    response = client.get("/api/v1/public/committee")
    assert response.status_code == 200
    body = response.json()
    assert [m["name"] for m in body] == ["Shown Trustee"]
    assert set(body[0]) == {"id", "name", "position", "photo_url"}
    assert "9999999999" not in response.text and "t@example.com" not in response.text


def test_private_endpoints_require_auth(client, db):
    donor = Donor(name="Private Donor", phone="9000000000", pan_number="ABCDE1234F")
    db.add(donor)
    db.commit()
    for path in [
        "/api/v1/donors/", f"/api/v1/donors/{donor.id}", f"/api/v1/donors/{donor.id}/receipt",
        "/api/v1/donations/", "/api/v1/donations/1/receipt", "/api/v1/temple-members/",
        "/api/v1/meta/stats", "/api/v1/meta/activity", "/api/v1/contacts/", "/api/v1/seva-tickets/",
        "/api/v1/finance/summary", "/api/v1/audit-logs/", "/api/v1/auth/admin/users",
    ]:
        assert client.get(path).status_code in (401, 404, 405), path
    # the legacy public receipt route is gone (was an IDOR by sequential id)
    assert client.get(f"/api/v1/donors/{donor.id}/receipt").status_code in (401, 404, 405)


def test_public_home_payload_is_public_safe(client, db):
    db.add(Pooja(name="Archana", pooja_type="daily", is_paid=False, is_active=True))
    db.add(Pooja(name="Hidden Pooja", pooja_type="daily", is_paid=False, is_active=False))
    db.commit()
    response = client.get("/api/v1/public/home")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"temple", "timings", "announcements", "festivals", "poojas"}
    assert [p["name"] for p in body["poojas"]] == ["Archana"]


def test_health_endpoints_leak_nothing(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert "environment" not in client.get("/").json()


def test_contact_form_public_ack_hides_content_and_rate_limits(client):
    payload = {"name": "Devotee", "email": "d@example.com", "subject": "Hello", "message": "Namaste!"}
    response = client.post("/api/v1/contacts/", json=payload)
    assert response.status_code == 201
    assert set(response.json()) == {"id", "status"}
    for _ in range(4):
        assert client.post("/api/v1/contacts/", json=payload).status_code == 201
    assert client.post("/api/v1/contacts/", json=payload).status_code == 429


def test_contact_honeypot_stores_nothing(client, db, admin):
    from app.models.contact import ContactMessage

    response = client.post("/api/v1/contacts/", json={
        "name": "Bot", "email": "bot@example.com", "subject": "Spam", "message": "buy now", "website": "http://x"})
    assert response.status_code == 201
    assert db.query(ContactMessage).count() == 0


def test_seva_booking_cannot_set_price_or_paid_seva(client, db):
    free = Pooja(name="Free Archana", pooja_type="daily", is_paid=False, is_active=True)
    paid = Pooja(name="Abhishekam", pooja_type="special", is_paid=True, suggested_amount=500, is_active=True)
    db.add_all([free, paid])
    db.commit()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    email, token = _verified_email(db, "ravi@example.com")

    ok = client.post("/api/v1/seva-tickets/", json={
        "seva_id": free.id, "devotee_name": "Ravi", "mobile_number": "9876543210", "seva_date": tomorrow,
        "email": email, "booking_token": token,
        "amount": 9999, "payment_status": "PAID", "seva_name": "Hacked"})
    assert ok.status_code == 200, ok.text
    ticket = ok.json()
    assert ticket["amount"] == 0 and ticket["payment_status"] == "FREE"
    assert ticket["seva_name"] == "Free Archana" and ticket["source"] == "ONLINE"
    assert ticket["email"] == email

    rejected = client.post("/api/v1/seva-tickets/", json={
        "seva_id": paid.id, "devotee_name": "Ravi", "mobile_number": "9876543210", "seva_date": tomorrow,
        "email": email, "booking_token": token})
    assert rejected.status_code == 400

    past = client.post("/api/v1/seva-tickets/", json={
        "seva_id": free.id, "devotee_name": "Ravi", "mobile_number": "9876543211",
        "seva_date": (date.today() - timedelta(days=1)).isoformat(),
        "email": email, "booking_token": token})
    assert past.status_code == 400


def test_security_response_shapes_have_no_hashes(client, super_admin):
    _, headers = super_admin
    text = client.get("/api/v1/auth/admin/users", headers=headers).text
    assert "hashed_password" not in text and "argon2" not in text
