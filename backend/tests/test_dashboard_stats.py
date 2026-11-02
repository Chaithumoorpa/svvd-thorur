"""GET /meta/stats zeroes out each count the caller's role can't otherwise
read (DonorRepository.count(), MemberRepository.count(), ticket counts,
pending messages) - a regression here would leak private counts to a role
that can't see the underlying records at all."""
from datetime import date, timedelta


def _seed(client, admin_headers):
    client.post("/api/v1/donors/", headers=admin_headers, json={"name": "Donor A"})
    client.post("/api/v1/temple-members/", headers=admin_headers, json={"name": "Member A", "phone": "9876543210"})
    pooja = client.post("/api/v1/poojas/", headers=admin_headers, json={"name": "Stats Archana"}).json()
    client.post("/api/v1/seva-tickets/admin", headers=admin_headers, json={
        "seva_id": pooja["id"], "devotee_name": "Ravi", "mobile_number": "9876543211",
        "seva_date": date.today().isoformat(), "payment_status": "FREE", "amount": 0})
    client.post("/api/v1/contacts", json={
        "name": "Devotee", "email": "d@example.com", "subject": "Query here", "message": "Hello there"})


def test_trustee_sees_donor_member_counts_but_not_tickets_or_messages(client, admin, trustee):
    _, admin_headers = admin
    _seed(client, admin_headers)

    _, trustee_headers = trustee
    stats = client.get("/api/v1/meta/stats", headers=trustee_headers).json()
    assert stats["donors"] == 1 and stats["members"] == 1
    assert stats["seva_tickets"] == 0 and stats["seva_tickets_today"] == 0  # no TICKETS_MANAGE
    assert stats["pending_messages"] == 0  # no MESSAGES_MANAGE


def test_staff_sees_tickets_and_messages_but_not_donors_or_members(client, admin, staff):
    _, admin_headers = admin
    _seed(client, admin_headers)

    _, staff_headers = staff
    stats = client.get("/api/v1/meta/stats", headers=staff_headers).json()
    assert stats["donors"] == 0 and stats["members"] == 0  # no DONORS_READ/MEMBERS_READ
    assert stats["seva_tickets"] == 1 and stats["seva_tickets_today"] == 1
    assert stats["pending_messages"] == 1


def test_super_admin_sees_everything(client, admin, super_admin):
    _, admin_headers = admin
    _seed(client, admin_headers)

    _, root_headers = super_admin
    stats = client.get("/api/v1/meta/stats", headers=root_headers).json()
    assert stats["donors"] == 1 and stats["members"] == 1
    assert stats["seva_tickets"] == 1 and stats["pending_messages"] == 1


def test_meta_stats_requires_dashboard_view(client):
    assert client.get("/api/v1/meta/stats").status_code == 401


def test_public_meta_endpoint_needs_no_auth(client):
    r = client.get("/api/v1/meta")
    assert r.status_code == 200 and r.json()["status"] == "active"
