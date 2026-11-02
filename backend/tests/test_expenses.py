"""Expense workflow: staff submit -> admin approves/rejects; corrections with a
reason; voiding; only approved expenses count; bills; monthly budgets."""
from datetime import date, timedelta
from unittest.mock import patch

from app.models.audit_log import AuditLog
from app.models.festival import Festival

URL = "/api/v1/finance/expenses"
TODAY = date.today().isoformat()


def _expense(client, headers, **extra):
    body = {"category": "POOJA_SUPPLIES", "description": "Ghee for deepam", "amount": "500",
            "payment_mode": "CASH", "paid_to": "Sri Lakshmi Stores", "expense_date": TODAY, **extra}
    r = client.post(URL, headers=headers, json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _total_expenses(client, headers):
    return client.get("/api/v1/finance/summary", headers=headers).json()["total_expenses"]


def test_admin_expense_is_approved_on_entry(client, admin):
    _, headers = admin
    row = _expense(client, headers)
    assert row["status"] == "APPROVED" and row["approved_by"] == row["submitted_by"]
    assert _total_expenses(client, headers) == 500


def test_staff_expense_waits_for_approval_and_only_then_counts(client, admin, staff, db):
    _, admin_h = admin
    _, staff_h = staff
    row = _expense(client, staff_h, amount="750")
    assert row["status"] == "PENDING" and row["approved_by"] is None
    assert _total_expenses(client, admin_h) == 0
    ledger = client.get("/api/v1/finance/ledger", headers=admin_h).json()
    assert ledger == []

    # staff can't approve their own
    assert client.post(f"{URL}/{row['id']}/approve", headers=staff_h).status_code == 403
    approved = client.post(f"{URL}/{row['id']}/approve", headers=admin_h).json()
    assert approved["status"] == "APPROVED" and approved["decided_at"]
    assert _total_expenses(client, admin_h) == 750
    # can't approve twice
    assert client.post(f"{URL}/{row['id']}/approve", headers=admin_h).status_code == 409
    assert db.query(AuditLog).filter(AuditLog.action == "APPROVE").count() == 1


def test_reject_needs_a_reason_and_never_counts(client, admin, staff):
    _, admin_h = admin
    _, staff_h = staff
    row = _expense(client, staff_h)
    assert client.post(f"{URL}/{row['id']}/reject", headers=admin_h, json={"reason": ""}).status_code == 422
    rejected = client.post(f"{URL}/{row['id']}/reject", headers=admin_h, json={"reason": "No bill attached"}).json()
    assert rejected["status"] == "REJECTED" and rejected["rejection_reason"] == "No bill attached"
    assert _total_expenses(client, admin_h) == 0
    # a rejected expense is closed
    assert client.patch(f"{URL}/{row['id']}", headers=staff_h, json={"amount": "1"}).status_code == 409


def test_staff_see_and_edit_only_their_own(client, admin, staff, make_user):
    _, admin_h = admin
    _, staff_h = staff
    _, other_h = make_user("STAFF", username="staff2")
    mine = _expense(client, staff_h, description="Camphor")
    _expense(client, other_h, description="Oil")
    _expense(client, admin_h, description="Electricity bill", category="UTILITIES")

    listed = client.get(URL, headers=staff_h).json()
    assert [e["description"] for e in listed] == ["Camphor"]
    assert len(client.get(URL, headers=admin_h).json()) == 3
    assert client.get(f"{URL}?status=PENDING", headers=admin_h).headers["x-total-count"] == "2"

    assert client.patch(f"{URL}/{mine['id']}", headers=other_h, json={"amount": "1"}).status_code == 403
    edited = client.patch(f"{URL}/{mine['id']}", headers=staff_h, json={"amount": "120.50"}).json()
    assert edited["amount"] == 120.5 and edited["status"] == "PENDING"


def test_correcting_an_approved_expense_needs_a_reason_and_is_audited(client, admin, staff, db):
    _, admin_h = admin
    _, staff_h = staff
    row = _expense(client, admin_h)
    assert client.patch(f"{URL}/{row['id']}", headers=staff_h, json={"amount": "1"}).status_code == 403
    assert client.patch(f"{URL}/{row['id']}", headers=admin_h, json={"amount": "450"}).status_code == 422
    r = client.patch(f"{URL}/{row['id']}", headers=admin_h,
                     json={"amount": "450", "reason": "Vendor gave a discount"})
    assert r.status_code == 200 and r.json()["amount"] == 450
    entry = db.query(AuditLog).filter(AuditLog.action == "UPDATE", AuditLog.entity_type == "expense").one()
    assert entry.changes["amount"] == {"from": "500.00", "to": "450"}
    assert entry.changes["reason"] == "Vendor gave a discount"
    assert _total_expenses(client, admin_h) == 450


def test_void_stops_an_expense_counting_but_keeps_it(client, admin):
    _, headers = admin
    row = _expense(client, headers)
    voided = client.post(f"{URL}/{row['id']}/void", headers=headers, json={"reason": "Entered twice"}).json()
    assert voided["status"] == "VOID" and voided["void_reason"] == "Entered twice"
    assert _total_expenses(client, headers) == 0
    assert client.get(f"{URL}?status=VOID", headers=headers).json()[0]["id"] == row["id"]
    assert client.post(f"{URL}/{row['id']}/void", headers=headers, json={"reason": "again"}).status_code == 409


def test_future_dates_and_unknown_festivals_are_rejected(client, admin):
    _, headers = admin
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    assert client.post(URL, headers=headers, json={
        "category": "OTHER", "description": "x" * 3, "amount": "1", "payment_mode": "CASH",
        "paid_to": "Shop", "expense_date": tomorrow}).status_code == 422
    assert client.post(URL, headers=headers, json={
        "category": "OTHER", "description": "Lights", "amount": "1", "payment_mode": "CASH",
        "paid_to": "Shop", "expense_date": TODAY, "festival_id": 999}).status_code == 422


def test_festival_tag_and_names_in_listing(client, admin, db):
    _, headers = admin
    festival = Festival(name="Vinayaka Chavithi", festival_date=date.today())
    db.add(festival)
    db.commit()
    _expense(client, headers, festival_id=festival.id, category="FESTIVAL", description="Pandal")
    row = client.get(f"{URL}?festival_id={festival.id}", headers=headers).json()[0]
    assert row["festival_name"] == "Vinayaka Chavithi" and row["submitted_by_name"] == "admin"


def test_bill_upload_and_private_link(client, admin, staff, make_user):
    _, admin_h = admin
    _, staff_h = staff
    with patch("app.services.storage_service.StorageService.enabled", True), \
         patch("app.services.storage_service.StorageService._client") as s3:
        s3.return_value.generate_presigned_post.return_value = {"url": "https://s3/upload", "fields": {"k": "v"}}
        s3.return_value.generate_presigned_url.return_value = "https://s3/signed-bill"
        upload = client.post(f"{URL}/bill-upload-url", headers=staff_h,
                             json={"content_type": "application/pdf"}).json()
        assert upload["key"].startswith("receipts/expense-bills/") and upload["key"].endswith(".pdf")
        row = _expense(client, staff_h, bill_key=upload["key"])
        assert row["has_bill"] is True and "bill_key" not in row

        link = client.get(f"{URL}/{row['id']}/bill", headers=admin_h).json()
        assert link == {"url": "https://s3/signed-bill", "content_type": "application/pdf"}
        _, other_h = make_user("STAFF", username="staff2")
        assert client.get(f"{URL}/{row['id']}/bill", headers=other_h).status_code == 403

    # a bill key outside the private bills folder is refused
    assert client.post(URL, headers=admin_h, json={
        "category": "OTHER", "description": "Lights", "amount": "1", "payment_mode": "CASH",
        "paid_to": "Shop", "expense_date": TODAY, "bill_key": "gallery/abc.jpg"}).status_code == 422


def test_monthly_budgets(client, admin, staff, trustee):
    _, admin_h = admin
    _, staff_h = staff
    _, trustee_h = trustee
    month = date.today().strftime("%Y-%m")
    r = client.put(f"/api/v1/finance/budgets/{month}", headers=admin_h, json={"lines": [
        {"category": "POOJA_SUPPLIES", "amount": "1000"}, {"category": "UTILITIES", "amount": "3000"}]})
    assert r.status_code == 200, r.text
    _expense(client, admin_h, amount="800")
    _expense(client, admin_h, amount="400")              # now over: 1200 of 1000
    _expense(client, staff_h, amount="250")              # pending - shown, not spent

    status = client.get(f"/api/v1/finance/budgets?month={month}", headers=trustee_h).json()
    pooja = next(l for l in status["lines"] if l["category"] == "POOJA_SUPPLIES")
    assert pooja == {"category": "POOJA_SUPPLIES", "budget": 1000, "spent": 1200, "pending": 250,
                     "remaining": -200, "percent_used": 120.0, "over_budget": True}
    utilities = next(l for l in status["lines"] if l["category"] == "UTILITIES")
    assert utilities["spent"] == 0 and utilities["over_budget"] is False
    assert status["total_budget"] == 4000 and status["total_spent"] == 1200

    # 0 removes a budget; copying starts next month from this one
    client.put(f"/api/v1/finance/budgets/{month}", headers=admin_h,
               json={"lines": [{"category": "UTILITIES", "amount": "0"}]})
    assert client.get(f"/api/v1/finance/budgets?month={month}", headers=admin_h).json()["total_budget"] == 1000
    nxt = (date.today().replace(day=28) + timedelta(days=5)).strftime("%Y-%m")
    copied = client.post(f"/api/v1/finance/budgets/{nxt}/copy-from/{month}", headers=admin_h).json()
    assert copied["total_budget"] == 1000
    assert client.put(f"/api/v1/finance/budgets/{month}", headers=admin_h, json={"lines": [
        {"category": "OTHER", "amount": "1"}, {"category": "OTHER", "amount": "2"}]}).status_code == 422
    assert client.get("/api/v1/finance/budgets?month=2026-13", headers=admin_h).status_code == 422


def test_legacy_expense_endpoint_still_records_approved(client, admin):
    _, headers = admin
    r = client.post("/api/v1/finance/expense", headers=headers, json={
        "category": "OTHER", "description": "Brooms", "amount": "60", "payment_mode": "CASH",
        "paid_to": "Market", "expense_date": TODAY})
    assert r.status_code == 201 and r.json()["status"] == "APPROVED"


def test_dashboard_counts_pending_expenses_for_approvers_only(client, admin, staff):
    _, admin_h = admin
    _, staff_h = staff
    _expense(client, staff_h)
    assert client.get("/api/v1/meta/stats", headers=admin_h).json()["pending_expenses"] == 1
    assert client.get("/api/v1/meta/stats", headers=staff_h).json()["pending_expenses"] == 0
