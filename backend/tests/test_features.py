"""Behaviour tests for features that were broken or unsafe before the review."""
from datetime import date, timedelta


# --- donors and receipts (used to crash: DonorCreate had no `amount`) ---------------

def test_create_donor_persists_amount_and_returns_it(client, admin_headers):
    r = client.post(
        "/api/v1/donors/",
        json={"name": "Lakshmi Devi", "phone": "9876543210", "amount": 1500, "donated_for": "annadanam"},
        headers=admin_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["amount"] == 1500
    assert body["donated_for"] == "annadanam"
    assert body["payment_mode"] == "CASH"
    assert body["donated_on"] is not None


def test_create_donor_rejects_zero_amount(client, admin_headers):
    r = client.post("/api/v1/donors/", json={"name": "X", "amount": 0}, headers=admin_headers)
    assert r.status_code == 400


def test_create_donor_rejects_oversize_input(client, admin_headers):
    r = client.post("/api/v1/donors/", json={"name": "N" * 500, "amount": 10}, headers=admin_headers)
    assert r.status_code == 422


def test_receipt_flow_generate_then_download_pdf(client, admin_headers, trustee_headers):
    donor = client.post(
        "/api/v1/donors/", json={"name": "Ravi Kumar", "amount": 501}, headers=admin_headers
    ).json()

    # Not generated yet
    assert client.get(f"/api/v1/donors/{donor['id']}/receipt", headers=admin_headers).status_code == 400

    gen = client.post(f"/api/v1/donors/{donor['id']}/generate-receipt", headers=admin_headers)
    assert gen.status_code == 200, gen.text
    number = gen.json()["receipt_number"]
    assert number.startswith("DON-")

    # Generating twice keeps the same number (persisted, not just set on the object)
    again = client.post(f"/api/v1/donors/{donor['id']}/generate-receipt", headers=admin_headers)
    assert again.json()["receipt_number"] == number

    pdf = client.get(f"/api/v1/donors/{donor['id']}/receipt", headers=trustee_headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


def test_receipt_is_not_public(client, admin_headers):
    donor = client.post("/api/v1/donors/", json={"name": "Priv", "amount": 10}, headers=admin_headers).json()
    client.post(f"/api/v1/donors/{donor['id']}/generate-receipt", headers=admin_headers)
    assert client.get(f"/api/v1/donors/{donor['id']}/receipt").status_code in (401, 403)


def test_update_donor_amount(client, admin_headers):
    donor = client.post("/api/v1/donors/", json={"name": "Upd", "amount": 10}, headers=admin_headers).json()
    r = client.put(f"/api/v1/donors/{donor['id']}", json={"amount": 99}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["amount"] == 99


# --- announcements: visibility window -------------------------------------------------

def test_announcement_visibility_window(client, admin_headers):
    today = date.today()

    def create(title, start=None, end=None, active=True):
        body = {"title": title, "message": "m"}
        if start:
            body["start_date"] = start.isoformat()
        if end:
            body["end_date"] = end.isoformat()
        r = client.post("/api/v1/announcements/", json=body, headers=admin_headers)
        assert r.status_code == 200, r.text
        ann_id = r.json()["id"]
        if not active:  # create schema has no is_active; deactivate via update
            r = client.put(f"/api/v1/announcements/{ann_id}", json={"is_active": False}, headers=admin_headers)
            assert r.status_code == 200, r.text
        return ann_id

    current = create("current", today - timedelta(days=1), today + timedelta(days=1))
    open_ended = create("open-ended")
    expired = create("expired", today - timedelta(days=10), today - timedelta(days=1))
    future = create("future", today + timedelta(days=2), today + timedelta(days=5))
    inactive = create("inactive", active=False)

    public_ids = {a["id"] for a in client.get("/api/v1/announcements/").json()}
    assert current in public_ids and open_ended in public_ids
    assert not ({expired, future, inactive} & public_ids)

    # Hidden ones 404 for the public but admins can still open them to edit
    assert client.get(f"/api/v1/announcements/{expired}").status_code == 404
    assert client.get(f"/api/v1/announcements/{expired}", headers=admin_headers).status_code == 200

    all_ids = {a["id"] for a in client.get("/api/v1/announcements/?show_all=true", headers=admin_headers).json()}
    assert {current, open_ended, expired, future, inactive} <= all_ids


# --- seva tickets ---------------------------------------------------------------------

def _make_pooja(client, admin_headers, name="Abhishekam"):
    r = client.post("/api/v1/poojas/", json={"name": name, "pooja_type": "daily"}, headers=admin_headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_public_booking_cannot_set_payment_or_amount(client, admin_headers):
    pooja_id = _make_pooja(client, admin_headers)
    r = client.post(
        "/api/v1/seva-tickets/",
        json={
            "seva_id": pooja_id,
            "seva_name": "ignored",
            "devotee_name": "Sita",
            "mobile_number": "98765 43210",
            "seva_date": (date.today() + timedelta(days=1)).isoformat(),
            "payment_status": "PAID",
            "amount": 5000,
        },
    )
    assert r.status_code == 200, r.text
    ticket = r.json()
    assert ticket["payment_status"] == "FREE"
    assert ticket["amount"] == 0
    assert ticket["source"] == "ONLINE"
    assert ticket["mobile_number"] == "9876543210"  # separators normalised
    assert ticket["seva_name"] == "Abhishekam"


def test_booking_rejects_bad_phone(client, admin_headers):
    pooja_id = _make_pooja(client, admin_headers, "Archana")
    r = client.post(
        "/api/v1/seva-tickets/",
        json={"seva_id": pooja_id, "devotee_name": "A", "mobile_number": "abc", "seva_date": date.today().isoformat()},
    )
    assert r.status_code == 422


def test_ticket_html_escapes_user_input(client, admin_headers, db):
    from app.services.seva_ticket_service import SevaTicketService
    from app.repositories.seva_ticket_repo import SevaTicketRepository
    from app.repositories.pooja_repo import PoojaRepository

    pooja_id = _make_pooja(client, admin_headers, "Homam")
    evil = '<script>alert(1)</script><img src="file:///etc/passwd">'
    ticket = client.post(
        "/api/v1/seva-tickets/",
        json={"seva_id": pooja_id, "devotee_name": evil, "mobile_number": "9123456780",
              "seva_date": (date.today() + timedelta(days=2)).isoformat()},
    ).json()

    service = SevaTicketService(SevaTicketRepository(db), PoojaRepository(db))
    stored = service.get_ticket(ticket["id"])
    html = service.generate_ticket_html(stored)
    assert "<script>" not in html
    assert 'src="file:///etc/passwd"' not in html
    assert "&lt;script&gt;" in html
    # The PDF renderer must still work with the escaped content
    assert service.generate_ticket_pdf(stored).getvalue().startswith(b"%PDF")


def test_booking_rate_limit(client, admin_headers):
    pooja_id = _make_pooja(client, admin_headers, "Kumkum")
    codes = []
    for i in range(12):
        r = client.post(
            "/api/v1/seva-tickets/",
            json={"seva_id": pooja_id, "devotee_name": f"D{i}", "mobile_number": f"90000000{i:02d}",
                  "seva_date": (date.today() + timedelta(days=3)).isoformat()},
        )
        codes.append(r.status_code)
    assert codes.count(200) == 10
    assert codes[-1] == 429


# --- contact form ---------------------------------------------------------------------

def _contact(**overrides):
    body = {"name": "Devotee", "email": "d@example.com", "subject": "Timings", "message": "Hello"}
    body.update(overrides)
    return body


def test_contact_submit_and_admin_can_read(client, admin_headers):
    assert client.post("/api/v1/contacts/", json=_contact()).status_code == 200
    listed = client.get("/api/v1/contacts/", headers=admin_headers)
    assert listed.status_code == 200 and len(listed.json()) >= 1


def test_contact_rejects_oversize_fields(client):
    assert client.post("/api/v1/contacts/", json=_contact(name="n" * 101)).status_code == 422
    assert client.post("/api/v1/contacts/", json=_contact(message="m" * 5001)).status_code == 422


def test_contact_rate_limited(client):
    codes = [client.post("/api/v1/contacts/", json=_contact()).status_code for _ in range(7)]
    assert codes[:5] == [200] * 5
    assert codes[5] == 429


# --- dashboard ------------------------------------------------------------------------

def test_dashboard_stats_and_real_activity(client, admin_headers):
    client.post("/api/v1/donors/", json={"name": "Act", "amount": 250}, headers=admin_headers)
    stats = client.get("/api/v1/meta/stats", headers=admin_headers)
    assert stats.status_code == 200 and stats.json()["donors"] >= 1

    activity = client.get("/api/v1/meta/activity", headers=admin_headers)
    assert activity.status_code == 200
    texts = [a["text"] for a in activity.json()]
    assert any("Donation of Rs. 250" in t for t in texts)
    assert not any("New member registered" == t for t in texts)  # old hard-coded fake entry
    assert all("Act" not in t.replace("Action", "") for t in texts)  # no donor names leaked
