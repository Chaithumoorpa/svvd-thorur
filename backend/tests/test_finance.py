"""Donors, donations, receipts and the finance ledger."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.finance import IncomeTransaction
from app.services.finance_service import FinanceService


def _donor(client, headers, **extra):
    response = client.post("/api/v1/donors/", headers=headers, json={"name": "Sita Devi", **extra})
    assert response.status_code == 201, response.text
    return response.json()


def test_donor_validation_and_pan_masking(client, admin, trustee):
    _, admin_headers = admin
    _, trustee_headers = trustee
    assert client.post("/api/v1/donors/", headers=admin_headers,
                       json={"name": "X", "pan_number": "bad"}).status_code == 422
    donor = _donor(client, admin_headers, pan_number="abcde1234f", phone="98765 43210")
    assert donor["pan_number"] == "ABCDE1234F"  # admins see the full PAN

    seen = client.get(f"/api/v1/donors/{donor['id']}", headers=trustee_headers).json()
    assert seen["pan_number"] == "AB*******F" and "ABCDE1234F" not in str(seen)
    listing = client.get("/api/v1/donors/", headers=trustee_headers).json()
    assert listing[0]["pan_number"].startswith("AB*")


def test_donation_posts_income_in_same_transaction(client, admin, db):
    _, headers = admin
    donor = _donor(client, headers)
    response = client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": "1500.50", "donation_type": "annadanam", "payment_mode": "UPI"})
    assert response.status_code == 201, response.text
    assert response.json()["amount"] == 1500.5 and response.json()["donor_name"] == "Sita Devi"

    income = db.query(IncomeTransaction).one()
    assert income.amount == Decimal("1500.50") and income.source_type.value == "DONATION"
    assert income.reference_id == f"donation:{response.json()['id']}"

    summary = client.get("/api/v1/finance/summary", headers=headers).json()
    assert summary["total_income"] == 1500.5 and summary["income_by_source"] == {"DONATION": 1500.5}

    # every donation posts to the ledger automatically - no opt-out
    client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": 10})
    assert db.query(IncomeTransaction).count() == 2

    row = client.get("/api/v1/donors/", headers=headers).json()[0]
    assert row["donation_count"] == 2 and row["total_donated"] == 1510.5


def test_donation_amount_edit_keeps_ledger_in_sync(client, admin, db):
    _, headers = admin
    donor = _donor(client, headers)
    created = client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": 100, "payment_mode": "CASH"}).json()

    client.put(f"/api/v1/donations/{created['id']}", headers=headers,
               json={"amount": 250, "payment_mode": "UPI"})

    income = db.query(IncomeTransaction).filter(
        IncomeTransaction.reference_id == f"donation:{created['id']}").one()
    assert income.amount == Decimal("250") and income.payment_mode.value == "UPI"


def test_manual_income_rejects_seva_and_donation_sources(client, admin):
    _, headers = admin
    for source in ("SEVA", "DONATION"):
        r = client.post("/api/v1/finance/income", headers=headers,
                        json={"source_type": source, "amount": 50, "payment_mode": "CASH"})
        assert r.status_code == 422, source

    for source in ("MANUAL", "HUNDI"):
        r = client.post("/api/v1/finance/income", headers=headers,
                        json={"source_type": source, "amount": 50, "payment_mode": "CASH"})
        assert r.status_code == 201, source


def test_paid_counter_ticket_posts_income_free_ticket_does_not(client, admin, db):
    _, headers = admin
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    pooja = client.post("/api/v1/poojas/", headers=headers,
                        json={"name": "Counter Archana", "is_paid": True, "suggested_amount": 50}).json()

    free = client.post("/api/v1/seva-tickets/admin", headers=headers, json={
        "seva_id": pooja["id"], "devotee_name": "Ravi", "mobile_number": "9876543210",
        "seva_date": tomorrow, "payment_status": "FREE", "amount": 0})
    assert free.status_code == 200, free.text
    assert db.query(IncomeTransaction).count() == 0

    paid = client.post("/api/v1/seva-tickets/admin", headers=headers, json={
        "seva_id": pooja["id"], "devotee_name": "Geeta", "mobile_number": "9876543211",
        "seva_date": tomorrow, "payment_status": "PAID", "amount": 101})
    assert paid.status_code == 200, paid.text

    income = db.query(IncomeTransaction).one()
    assert income.source_type.value == "SEVA" and income.amount == Decimal("101")
    assert income.reference_id == f"seva_ticket:{paid.json()['id']}"

    summary = client.get("/api/v1/finance/summary", headers=headers).json()
    assert summary["income_by_source"] == {"SEVA": 101.0}


def test_donation_validation(client, admin):
    _, headers = admin
    donor = _donor(client, headers)
    for amount in (0, -5, "abc", "10.999"):
        r = client.post("/api/v1/donations/", headers=headers, json={"donor_id": donor["id"], "amount": amount})
        assert r.status_code == 422, amount
    assert client.post("/api/v1/donations/", headers=headers,
                       json={"donor_id": 9999, "amount": 10}).status_code == 400
    assert client.post("/api/v1/donations/", headers=headers, json={
        "donor_id": donor["id"], "amount": 10, "donation_type": "nonsense"}).status_code == 422


def test_receipts_are_sequential_idempotent_and_private(client, admin, trustee, staff):
    _, headers = admin
    donor = _donor(client, headers, name="<b>Bold</b> Donor")
    ids = [client.post("/api/v1/donations/", headers=headers,
                       json={"donor_id": donor["id"], "amount": 100 * (i + 1)}).json()["id"] for i in range(2)]

    assert client.get(f"/api/v1/donations/{ids[0]}/receipt", headers=headers).status_code == 400  # not issued
    first = client.post(f"/api/v1/donations/{ids[0]}/receipt", headers=headers).json()
    again = client.post(f"/api/v1/donations/{ids[0]}/receipt", headers=headers).json()
    second = client.post(f"/api/v1/donations/{ids[1]}/receipt", headers=headers).json()
    year = datetime.now().year
    assert first["receipt_number"] == again["receipt_number"] == f"DON-{year}-000001"
    assert second["receipt_number"] == f"DON-{year}-000002"

    pdf = client.get(f"/api/v1/donations/{ids[0]}/receipt", headers=headers)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    _, trustee_headers = trustee
    assert client.get(f"/api/v1/donations/{ids[0]}/receipt", headers=trustee_headers).status_code == 200
    assert client.post(f"/api/v1/donations/{ids[0]}/receipt", headers=trustee_headers).status_code == 403
    _, staff_headers = staff
    assert client.get(f"/api/v1/donations/{ids[0]}/receipt", headers=staff_headers).status_code == 403

    # amount is frozen once a receipt exists
    frozen = client.put(f"/api/v1/donations/{ids[0]}", headers=headers, json={"amount": 5})
    assert frozen.status_code == 409
    assert client.put(f"/api/v1/donations/{ids[0]}", headers=headers, json={"purpose": "Roof"}).status_code == 200


def test_donation_list_filters_and_order(client, admin):
    _, headers = admin
    donor = _donor(client, headers)
    for day, amount in [(3, 30), (1, 10), (2, 20)]:
        client.post("/api/v1/donations/", headers=headers, json={
            "donor_id": donor["id"], "amount": amount, "donated_on": f"2026-03-0{day}T10:00:00"})
    everything = client.get("/api/v1/donations/", headers=headers).json()
    assert [d["amount"] for d in everything] == [30, 20, 10]
    ranged = client.get("/api/v1/donations/?start_date=2026-03-02&end_date=2026-03-02", headers=headers).json()
    assert [d["amount"] for d in ranged] == [20]  # end date is inclusive


# --------------------------------------------------------------------- finance
def _add(client, headers, kind, **body):
    return client.post(f"/api/v1/finance/{kind}", headers=headers, json=body)


def test_income_expense_summary_and_decimal_precision(client, admin):
    _, headers = admin
    assert _add(client, headers, "income", source_type="HUNDI", amount="0.10", payment_mode="CASH").status_code == 201
    assert _add(client, headers, "income", source_type="HUNDI", amount="0.20", payment_mode="CASH").status_code == 201
    assert _add(client, headers, "expense", category="OTHER", description="Flowers", amount="0.05",
                payment_mode="CASH", paid_to="Vendor", expense_date=date.today().isoformat()).status_code == 201
    summary = client.get("/api/v1/finance/summary", headers=headers).json()
    # 0.1 + 0.2 - 0.05 is exactly 0.25 with Decimal (float math would give 0.25000000000000006)
    assert summary["balance"] == 0.25 and summary["total_income"] == 0.3


def test_finance_rejects_bad_amounts(client, admin):
    _, headers = admin
    for amount in (0, -1, "1e10"):
        assert _add(client, headers, "income", source_type="MANUAL", amount=amount,
                    payment_mode="CASH").status_code == 422


def test_ledger_mixed_dates_sorted_and_inclusive(client, admin, db):
    """Regression: sorting datetime (income) with date (expense) used to raise TypeError."""
    _, headers = admin
    # "today" as the database clock sees it (the DB and the test process may sit in different
    # timezones, e.g. UTC vs IST around midnight)
    income = _add(client, headers, "income", source_type="HUNDI", amount=100, payment_mode="CASH")
    today = date.fromisoformat(income.json()["received_at"][:10])
    _add(client, headers, "expense", category="MATERIAL", description="Oil", amount=40,
         payment_mode="UPI", paid_to="Shop", expense_date=today.isoformat())
    _add(client, headers, "expense", category="MATERIAL", description="Old bill", amount=5,
         payment_mode="UPI", paid_to="Shop", expense_date=(today - timedelta(days=30)).isoformat())

    ledger = client.get("/api/v1/finance/ledger", headers=headers)
    assert ledger.status_code == 200
    assert ledger.headers["X-Total-Count"] == "3"
    amounts = [e["amount"] for e in ledger.json()]
    assert amounts == [-40, 100, -5]  # same-day expense (end of day) first, oldest last

    only_today = client.get(f"/api/v1/finance/ledger?start_date={today}&end_date={today}", headers=headers)
    assert only_today.headers["X-Total-Count"] == "2"  # end date includes the whole day

    page = client.get("/api/v1/finance/ledger?page=2&page_size=2", headers=headers).json()
    assert [e["amount"] for e in page] == [-5]


def test_ledger_exports(client, admin):
    _, headers = admin
    today = date.today().isoformat()
    _add(client, headers, "expense", category="OTHER", description="=HYPERLINK(\"http://evil\")", amount=1,
         payment_mode="CASH", paid_to="X Y", expense_date=today)
    csv_response = client.get(f"/api/v1/finance/ledger/csv?start_date={today}&end_date={today}", headers=headers)
    assert csv_response.status_code == 200
    assert "'Expense: =HYPERLINK" not in csv_response.text  # the formula is not at the start of a cell
    assert ",=HYPERLINK" not in csv_response.text
    pdf = client.get(f"/api/v1/finance/ledger/pdf?start_date={today}&end_date={today}", headers=headers)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    report = client.get(f"/api/v1/finance/reports/monthly?year={date.today().year}&month={date.today().month}",
                        headers=headers)
    assert report.status_code == 200 and report.json()["total_expenses"] == 1


def test_finance_service_layer_direct(db, admin):
    from app.schemas.finance import IncomeTransactionCreate

    user, _ = admin
    row = FinanceService.add_income(db, IncomeTransactionCreate(
        source_type="MANUAL", amount="12.34", payment_mode="CASH"), user.id)
    assert row.amount == Decimal("12.34") and row.received_by == user.id


def test_audit_log_access_and_content(client, admin, super_admin):
    _, headers = admin
    _add(client, headers, "income", source_type="HUNDI", amount=50, payment_mode="CASH", notes="secret note")
    assert client.get("/api/v1/audit-logs/", headers=headers).status_code == 403
    _, root_headers = super_admin
    logs = client.get("/api/v1/audit-logs/?entity_type=income", headers=root_headers).json()
    assert len(logs) == 1 and logs[0]["actor_username"] == "admin" and logs[0]["action"] == "CREATE"
    assert client.get("/api/v1/meta/activity", headers=root_headers).json()[0]["actor"] == "admin"
    # newest first and stable
    all_logs = client.get("/api/v1/audit-logs/", headers=root_headers).json()
    assert [l["id"] for l in all_logs] == sorted((l["id"] for l in all_logs), reverse=True)


def test_passwords_never_reach_the_audit_log(client, super_admin, db):
    from app.models.audit_log import AuditLog

    _, headers = super_admin
    client.post("/api/v1/auth/admin/users", headers=headers,
                json={"username": "clerk1", "password": "SuperSecret99", "roles": ["STAFF"]})
    client.patch("/api/v1/auth/admin/users/1", headers=headers, json={"password": "AnotherSecret99"})
    dump = " ".join(f"{l.summary} {l.changes}" for l in db.query(AuditLog).all())
    assert "SuperSecret99" not in dump and "AnotherSecret99" not in dump
