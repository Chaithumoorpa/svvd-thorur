"""Inventory: stock only moves through movements; purchases create expenses;
donations in kind get numbered acknowledgements; usage is costed at the
weighted average and adds up to a festival's cost; valuables are verified."""
from datetime import date
from decimal import Decimal

from app.models.festival import Festival
from app.models.finance import ExpenseTransaction
from app.models.inventory import InventoryItem, StockMovement
from app.models.pooja import Pooja

INV = "/api/v1/inventory"
TODAY = date.today().isoformat()


def _item(client, headers, **extra):
    body = {"name": "Cow ghee", "kind": "CONSUMABLE", "category": "Oils & ghee", "unit": "kg",
            "reorder_level": "2", **extra}
    r = client.post(f"{INV}/items", headers=headers, json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _buy(client, headers, item_id, qty, cost, **extra):
    r = client.post(f"{INV}/purchases", headers=headers, json={
        "item_id": item_id, "quantity": str(qty), "total_cost": str(cost), "vendor": "Sri Lakshmi Stores",
        "payment_mode": "CASH", "movement_date": TODAY, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def _use(client, headers, item_id, qty, **extra):
    return client.post(f"{INV}/usage", headers=headers, json={
        "item_id": item_id, "quantity": str(qty), "movement_date": TODAY, **extra})


def test_purchase_adds_stock_and_records_the_expense(client, admin, db):
    _, headers = admin
    item = _item(client, headers)
    movement = _buy(client, headers, item["id"], 5, 3000)
    assert movement["type"] == "PURCHASE" and movement["balance_after"] == "5.000"
    assert movement["unit_cost"] == "600.0000" and movement["expense_status"] == "APPROVED"

    expense = db.query(ExpenseTransaction).one()
    assert str(expense.id) == movement["expense_id"]
    assert expense.amount == Decimal("3000.00") and expense.category.value == "POOJA_SUPPLIES"
    assert expense.description == "Stock purchase: 5 kg Cow ghee" and expense.paid_to == "Sri Lakshmi Stores"
    assert client.get("/api/v1/finance/summary", headers=headers).json()["total_expenses"] == 3000
    listed = client.get("/api/v1/finance/expenses", headers=headers).json()[0]
    assert listed["inventory_item_id"] == item["id"]


def test_staff_purchase_stocks_goods_but_expense_waits_for_approval(client, admin, staff, db):
    _, admin_h = admin
    _, staff_h = staff
    item = _item(client, admin_h)
    movement = _buy(client, staff_h, item["id"], 2, 1300)
    assert movement["expense_status"] == "PENDING"
    assert client.get(f"{INV}/items/{item['id']}", headers=staff_h).json()["quantity"] == "2.000"
    assert client.get("/api/v1/finance/summary", headers=admin_h).json()["total_expenses"] == 0


def test_weighted_average_cost_and_usage_value(client, admin):
    _, headers = admin
    item = _item(client, headers)
    _buy(client, headers, item["id"], 4, 2000)     # 500/kg
    _buy(client, headers, item["id"], 1, 1000)     # 1000/kg -> avg (2000+1000)/5 = 600
    assert client.get(f"{INV}/items/{item['id']}", headers=headers).json()["avg_unit_cost"] == "600.0000"
    used = _use(client, headers, item["id"], "1.5").json()
    assert used["quantity"] == "-1.500" and used["balance_after"] == "3.500" and used["total_value"] == -900


def test_cannot_use_more_than_in_stock_or_use_a_valuable(client, admin, staff):
    _, admin_h = admin
    _, staff_h = staff
    item = _item(client, admin_h, opening_quantity="1", opening_unit_cost="500")
    r = _use(client, staff_h, item["id"], 2)
    assert r.status_code == 409 and "Only 1 kg of Cow ghee in stock" in r.json()["detail"]
    lamp = _item(client, admin_h, name="Silver deepam", kind="ASSET", category="Lamps", unit="pcs",
                 opening_quantity="1", material="SILVER", weight_grams="350")
    assert _use(client, admin_h, lamp["id"], 1).status_code == 409


def test_opening_stock_low_stock_flag_and_summary(client, admin, staff):
    _, admin_h = admin
    _, staff_h = staff
    item = _item(client, admin_h, opening_quantity="3", opening_unit_cost="550")
    assert item["quantity"] == "3.000" and item["low_stock"] is False and item["stock_value"] == 1650
    _use(client, staff_h, item["id"], 1)
    now = client.get(f"{INV}/items/{item['id']}", headers=staff_h).json()
    assert now["low_stock"] is True
    assert [i["id"] for i in client.get(f"{INV}/items?low_stock=true", headers=staff_h).json()] == [item["id"]]
    assert client.get("/api/v1/meta/stats", headers=staff_h).json()["low_stock_items"] == 1
    summary = client.get(f"{INV}/summary", headers=staff_h).json()
    assert summary["consumables"] == 1 and summary["low_stock"] == 1 and summary["stock_value"] == 1100


def test_donation_in_kind_is_numbered_and_printable(client, admin, staff, db):
    _, admin_h = admin
    _, staff_h = staff
    rice = _item(client, admin_h, name="Rice", category="Grains", unit="kg")
    first = client.post(f"{INV}/donations-in", headers=staff_h, json={
        "item_id": rice["id"], "quantity": "25", "donor_name": "Ramesh Goud", "donor_phone": "98765 43210",
        "movement_date": TODAY}).json()
    second = client.post(f"{INV}/donations-in", headers=staff_h, json={
        "item_id": rice["id"], "quantity": "10", "donor_name": "Lakshmi", "estimated_value": "500",
        "movement_date": TODAY}).json()
    year = date.today().year
    assert (first["receipt_number"], second["receipt_number"]) == (f"IK-{year}-0001", f"IK-{year}-0002")
    assert first["total_value"] is None and second["total_value"] == 500
    assert db.get(InventoryItem, rice["id"]).quantity == Decimal("35.000")
    assert db.query(ExpenseTransaction).count() == 0  # a gift is not spending

    pdf = client.get(f"{INV}/movements/{first['id']}/receipt", headers=admin_h)
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF") and f"IK-{year}-0001".encode() in pdf.headers["content-disposition"].encode()
    usage = _use(client, admin_h, rice["id"], 1).json()
    assert client.get(f"{INV}/movements/{usage['id']}/receipt", headers=admin_h).status_code == 400


def test_stock_count_adjustment_and_write_off_are_admin_only(client, admin, staff):
    _, admin_h = admin
    _, staff_h = staff
    item = _item(client, admin_h, opening_quantity="10", opening_unit_cost="100")
    body = {"item_id": item["id"], "counted_quantity": "9.5", "reason": "Monthly stock count",
            "movement_date": TODAY}
    assert client.post(f"{INV}/adjustments", headers=staff_h, json=body).status_code == 403
    adj = client.post(f"{INV}/adjustments", headers=admin_h, json=body).json()
    assert adj["quantity"] == "-0.500" and adj["balance_after"] == "9.500"
    assert client.post(f"{INV}/adjustments", headers=admin_h, json=body).status_code == 409  # already matches

    wo = client.post(f"{INV}/write-offs", headers=admin_h, json={
        "item_id": item["id"], "quantity": "2", "reason": "Gone rancid", "movement_date": TODAY}).json()
    assert wo["balance_after"] == "7.500" and wo["notes"] == "Gone rancid"


def test_history_always_adds_up_to_the_stock(client, admin, db):
    _, headers = admin
    item = _item(client, headers, opening_quantity="2", opening_unit_cost="500")
    _buy(client, headers, item["id"], 3, 1800)
    _use(client, headers, item["id"], "1.25")
    client.post(f"{INV}/write-offs", headers=headers, json={
        "item_id": item["id"], "quantity": "0.25", "reason": "Spilled", "movement_date": TODAY})
    moves = db.query(StockMovement).filter(StockMovement.item_id == item["id"]).all()
    assert sum(m.quantity for m in moves) == db.get(InventoryItem, item["id"]).quantity == Decimal("3.500")
    history = client.get(f"{INV}/movements?item_id={item['id']}", headers=headers)
    assert history.headers["x-total-count"] == "4"


def test_festival_cost_counts_usage_and_tagged_expenses_without_double_counting(client, admin, db):
    _, headers = admin
    festival = Festival(name="Vinayaka Chavithi", festival_date=date.today())
    seva = Pooja(name="Ganapathi Homam")
    db.add_all([festival, seva])
    db.commit()
    ghee = _item(client, headers)
    _buy(client, headers, ghee["id"], 10, 6000)                      # 600/kg - not a festival cost by itself
    _use(client, headers, ghee["id"], 3, festival_id=festival.id)   # 1800 for the festival
    _use(client, headers, ghee["id"], 1, pooja_id=seva.id)          # a seva, not the festival
    client.post("/api/v1/finance/expenses", headers=headers, json={
        "category": "FESTIVAL", "description": "Pandal and lights", "amount": "5000", "payment_mode": "CASH",
        "paid_to": "Decorators", "expense_date": TODAY, "festival_id": festival.id})

    costs = client.get(f"{INV}/festival-costs", headers=headers).json()
    assert len(costs) == 1
    cost = costs[0]
    assert cost["festival_name"] == "Vinayaka Chavithi"
    assert (cost["stock_used_value"], cost["expenses_total"], cost["total_cost"]) == (1800, 5000, 6800)
    assert cost["items"] == [{"item_name": "Cow ghee", "unit": "kg", "quantity": "3.000", "value": 1800}]
    seva_use = client.get(f"{INV}/movements?pooja_id={seva.id}", headers=headers).json()
    assert seva_use[0]["pooja_name"] == "Ganapathi Homam"


def test_valuables_register_and_verification(client, admin, staff, trustee):
    _, admin_h = admin
    _, staff_h = staff
    _, trustee_h = trustee
    crown = _item(client, admin_h, name="Kireetam", kind="ASSET", category="Ornaments", unit="pcs",
                  opening_quantity="1", material="GOLD", weight_grams="120.5", estimated_value="850000",
                  identification="Donated 2019, inscription on base")
    assert crown["condition"] == "GOOD" and crown["stock_value"] == 850000
    summary = client.get(f"{INV}/summary", headers=trustee_h).json()
    assert summary["valuables"] == 1 and summary["valuables_unverified"] == 1

    body = {"verified_on": TODAY, "condition": "GOOD", "weight_grams": "120.4"}
    assert client.post(f"{INV}/items/{crown['id']}/verifications", headers=staff_h, json=body).status_code == 403
    ok = client.post(f"{INV}/items/{crown['id']}/verifications", headers=admin_h, json=body).json()
    assert ok["weight_mismatch"] is False and ok["verified_by_name"] == "admin"
    off = client.post(f"{INV}/items/{crown['id']}/verifications", headers=admin_h,
                      json={**body, "weight_grams": "110", "condition": "NEEDS_REPAIR"}).json()
    assert off["weight_mismatch"] is True
    item = client.get(f"{INV}/items/{crown['id']}", headers=trustee_h).json()
    assert item["condition"] == "NEEDS_REPAIR" and item["last_verified_on"] == TODAY
    assert client.get(f"{INV}/summary", headers=trustee_h).json()["valuables_unverified"] == 0
    assert len(client.get(f"{INV}/items/{crown['id']}/verifications", headers=trustee_h).json()) == 2

    ghee = _item(client, admin_h)
    assert client.post(f"{INV}/items/{ghee['id']}/verifications", headers=admin_h, json=body).status_code == 409


def test_items_are_unique_editable_and_only_deleted_without_history(client, admin, staff):
    _, admin_h = admin
    _, staff_h = staff
    item = _item(client, admin_h)
    r = client.post(f"{INV}/items", headers=admin_h, json={
        "name": "cow GHEE", "kind": "CONSUMABLE", "category": "x", "unit": "kg"})
    assert r.status_code == 409
    assert client.patch(f"{INV}/items/{item['id']}", headers=staff_h, json={"location": "Store"}).status_code == 403
    edited = client.patch(f"{INV}/items/{item['id']}", headers=admin_h,
                          json={"location": "Store room", "reorder_level": "5"}).json()
    assert edited["location"] == "Store room" and edited["reorder_level"] == "5.000"
    # quantity is not editable directly
    client.patch(f"{INV}/items/{item['id']}", headers=admin_h, json={"quantity": "999"})
    assert client.get(f"{INV}/items/{item['id']}", headers=admin_h).json()["quantity"] == "0.000"

    _buy(client, admin_h, item["id"], 1, 600)
    assert client.delete(f"{INV}/items/{item['id']}", headers=admin_h).status_code == 409
    client.patch(f"{INV}/items/{item['id']}", headers=admin_h, json={"is_active": False})
    assert client.get(f"{INV}/items", headers=admin_h).json() == []
    assert client.post(f"{INV}/purchases", headers=admin_h, json={
        "item_id": item["id"], "quantity": "1", "total_cost": "1", "vendor": "Shop", "payment_mode": "CASH",
        "movement_date": TODAY}).status_code == 409

    mistake = _item(client, admin_h, name="Typo item")
    assert client.delete(f"{INV}/items/{mistake['id']}", headers=admin_h).status_code == 204
