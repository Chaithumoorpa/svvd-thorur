"""Deleting a seva ticket is Admin/Super Admin only - deliberately narrower
than tickets:manage, which STAFF also holds, since a paid counter ticket's
deletion also has to clean up its linked finance ledger entry."""
from datetime import date, timedelta

from app.models.finance import IncomeTransaction


def _pooja(client, headers, is_paid=True):
    return client.post("/api/v1/poojas/", headers=headers,
                       json={"name": "Counter Archana", "is_paid": is_paid, "suggested_amount": 50}).json()


def _paid_ticket(client, headers, pooja_id):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = client.post("/api/v1/seva-tickets/admin", headers=headers, json={
        "seva_id": pooja_id, "devotee_name": "Geeta", "mobile_number": "9876543211",
        "seva_date": tomorrow, "payment_status": "PAID", "amount": 101})
    assert r.status_code == 200, r.text
    return r.json()


def test_admin_can_delete_ticket_and_its_linked_income(client, admin, db):
    _, headers = admin
    pooja = _pooja(client, headers)
    ticket = _paid_ticket(client, headers, pooja["id"])
    assert db.query(IncomeTransaction).count() == 1

    r = client.delete(f"/api/v1/seva-tickets/{ticket['id']}", headers=headers)
    assert r.status_code == 200, r.text

    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}", headers=headers).status_code == 404
    assert db.query(IncomeTransaction).count() == 0


def test_deleting_a_free_ticket_touches_no_income(client, admin, db):
    _, headers = admin
    pooja = _pooja(client, headers, is_paid=False)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    ticket = client.post("/api/v1/seva-tickets/admin", headers=headers, json={
        "seva_id": pooja["id"], "devotee_name": "Ravi", "mobile_number": "9876543210",
        "seva_date": tomorrow, "payment_status": "FREE", "amount": 0}).json()

    r = client.delete(f"/api/v1/seva-tickets/{ticket['id']}", headers=headers)
    assert r.status_code == 200
    assert db.query(IncomeTransaction).count() == 0


def test_staff_cannot_delete_ticket(client, admin, staff):
    _, admin_headers = admin
    _, staff_headers = staff
    pooja = _pooja(client, admin_headers)
    ticket = _paid_ticket(client, admin_headers, pooja["id"])

    r = client.delete(f"/api/v1/seva-tickets/{ticket['id']}", headers=staff_headers)
    assert r.status_code == 403
    assert client.get(f"/api/v1/seva-tickets/{ticket['id']}", headers=admin_headers).status_code == 200


def test_super_admin_can_delete_ticket(client, admin, super_admin):
    _, admin_headers = admin
    _, super_headers = super_admin
    pooja = _pooja(client, admin_headers)
    ticket = _paid_ticket(client, admin_headers, pooja["id"])

    r = client.delete(f"/api/v1/seva-tickets/{ticket['id']}", headers=super_headers)
    assert r.status_code == 200


def test_delete_nonexistent_ticket_404s(client, admin):
    _, headers = admin
    import uuid
    r = client.delete(f"/api/v1/seva-tickets/{uuid.uuid4()}", headers=headers)
    assert r.status_code == 404
