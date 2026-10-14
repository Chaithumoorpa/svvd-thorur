"""Admin analytics: finance, inventory and audit-log summaries, plus failed
sign-ins now being recorded in the audit log."""
from datetime import date, datetime, timedelta

from app.models.audit_log import AuditLog
from app.models.festival import Festival
from app.services.analytics_service import IST, month_keys

TODAY = date.today().isoformat()
THIS_MONTH = date.today().strftime("%Y-%m")


def _expense(client, headers, amount, paid_to="Lakshmi Stores", category="POOJA_SUPPLIES", **extra):
    r = client.post("/api/v1/finance/expenses", headers=headers, json={
        "category": category, "description": "Supplies", "amount": str(amount), "payment_mode": "CASH",
        "paid_to": paid_to, "expense_date": TODAY, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def test_month_keys_end_with_this_month():
    assert month_keys(3, date(2026, 2, 10)) == ["2025-12", "2026-01", "2026-02"]


def test_finance_analytics(client, admin, staff):
    _, headers = admin
    _, staff_h = staff
    client.post("/api/v1/finance/income", headers=headers,
                json={"source_type": "HUNDI", "amount": "5000", "payment_mode": "CASH"})
    client.post("/api/v1/finance/income", headers=headers,
                json={"source_type": "MANUAL", "amount": "1200", "payment_mode": "UPI"})
    _expense(client, headers, 800)
    _expense(client, headers, 450, paid_to="lakshmi stores ")      # same payee, different spelling
    _expense(client, headers, 2000, paid_to="TSNPDCL", category="UTILITIES")
    _expense(client, staff_h, 999)                                   # pending - never counted
    voided = _expense(client, headers, 300)
    client.post(f"/api/v1/finance/expenses/{voided['id']}/void", headers=headers, json={"reason": "Twice"})
    donor = client.post("/api/v1/donors/", headers=headers, json={"name": "Sita Devi"}).json()
    client.post("/api/v1/donations/", headers=headers, json={"donor_id": donor["id"], "amount": "1001"})

    data = client.get("/api/v1/analytics/finance?months=6", headers=headers).json()
    assert [m["month"] for m in data["months"]] == month_keys(6)
    now = data["months"][-1]
    assert (now["income"], now["expenses"], now["net"]) == (7201, 3250, 3951)
    assert data["totals"] == {"income": 7201, "expenses": 3250, "net": 3951}
    assert data["expense_by_category"][0] == {"name": "UTILITIES", "amount": 2000}
    assert data["top_payees"][0] == {"name": "Tsnpdcl", "count": 1, "amount": 2000}
    assert data["top_payees"][1] == {"name": "Lakshmi Stores", "count": 2, "amount": 1250}
    assert {m["mode"] for m in data["payment_modes"]} == {"CASH", "UPI"}
    assert data["donations"] == {"count": 1, "total": 1001, "donors": 1, "average": 1001}
    assert {r["name"] for r in data["income_by_source"]} == {"HUNDI", "MANUAL", "DONATION"}


def test_inventory_analytics(client, admin, db):
    _, headers = admin
    festival = Festival(name="Vinayaka Chavithi", festival_date=date.today())
    db.add(festival)
    db.commit()
    item = client.post("/api/v1/inventory/items", headers=headers, json={
        "name": "Cow ghee", "kind": "CONSUMABLE", "category": "Oils & ghee", "unit": "kg",
        "opening_quantity": "10", "opening_unit_cost": "600"}).json()
    client.post("/api/v1/inventory/usage", headers=headers, json={
        "item_id": item["id"], "quantity": "2", "movement_date": TODAY, "festival_id": festival.id})
    client.post("/api/v1/inventory/write-offs", headers=headers, json={
        "item_id": item["id"], "quantity": "0.5", "reason": "Spoiled", "movement_date": TODAY})
    client.post("/api/v1/inventory/donations-in", headers=headers, json={
        "item_id": item["id"], "quantity": "1", "donor_name": "Ramesh", "movement_date": TODAY})

    data = client.get("/api/v1/analytics/inventory?months=3", headers=headers).json()
    assert data["stock_by_category"] == [{"name": "Oils & ghee", "amount": 5100}]   # 8.5 kg x 600
    now = data["consumption"][-1]
    assert now == {"month": THIS_MONTH, "used": 1200, "written_off": 300, "donated_in": 1}
    assert data["top_used"] == [{"item_name": "Cow ghee", "unit": "kg", "quantity": "2.000", "value": 1200}]


def test_failed_sign_ins_are_audited(client, make_user, db):
    make_user("ADMIN", username="alice")
    r = client.post("/api/v1/auth/login", json={"username": "alice", "password": "wrong-password"})
    assert r.status_code == 401
    client.post("/api/v1/auth/login", json={"username": "nobody", "password": "x" * 10})
    failed = db.query(AuditLog).filter(AuditLog.action == "LOGIN_FAILED").all()
    assert len(failed) == 2
    assert {f.actor_username for f in failed} == {"alice", "nobody"}
    assert all(f.actor_id is None for f in failed)
    assert "wrong password or unknown account" in failed[0].summary


def test_audit_analytics(client, make_user, db):
    boss, headers = make_user("SUPER_ADMIN", username="boss")
    client.post("/api/v1/auth/login", json={"username": "boss", "password": "nope-nope"})
    client.post("/api/v1/announcements/", headers=headers, json={"title": "Festival notice"})
    ann = client.post("/api/v1/announcements/", headers=headers, json={"title": "Old notice"}).json()
    client.delete(f"/api/v1/announcements/{ann['id']}", headers=headers)
    # a change at 11:30 pm IST yesterday - off-hours
    late = datetime.combine(date.today() - timedelta(days=1), datetime.min.time()) + timedelta(hours=23, minutes=30) - IST
    db.add(AuditLog(actor_id=boss.id, actor_username="boss", action="UPDATE", entity_type="temple",
                    summary="Late change", created_at=late, updated_at=late))
    db.commit()

    data = client.get("/api/v1/analytics/audit?days=7", headers=headers).json()
    t = data["totals"]
    assert t["failed_logins"] == 1 and t["deletions"] == 1 and t["off_hours"] >= 1
    assert t["events"] == sum(d["count"] for d in data["per_day"]) == sum(data["by_hour"])
    assert len(data["per_day"]) == 7 and data["per_day"][-1]["date"] == (datetime.utcnow() + IST).date().isoformat()
    assert data["by_hour"][23] >= 1
    assert data["by_actor"][0]["name"] == "boss" and data["by_actor"][0]["deletions"] == 1
    assert {"name": "DELETE", "count": 1} in data["by_action"]
    kinds = {(e["action"], e["off_hours"]) for e in data["sensitive"]}
    assert ("DELETE", False) in kinds or ("DELETE", True) in kinds
    assert ("UPDATE", True) in kinds and any(a == "LOGIN_FAILED" for a, _ in kinds)
    assert data["failed_login_ips"][0]["count"] == 1


def test_analytics_permissions(client, make_user):
    for role, allowed in (("SUPER_ADMIN", {"finance", "inventory", "audit"}),
                          ("ADMIN", {"finance", "inventory"}),
                          ("TRUSTEE", {"finance", "inventory"}),
                          ("STAFF", {"inventory"}),
                          ("GENERAL_USER", set())):
        _, headers = make_user(role, username=f"u_{role.lower()}")
        for section in ("finance", "inventory", "audit"):
            code = client.get(f"/api/v1/analytics/{section}", headers=headers).status_code
            assert (code == 200) == (section in allowed), (role, section, code)
    assert client.get("/api/v1/analytics/audit?days=0", headers=headers).status_code in (403, 422)
