"""Read-only analytics for the admin Analytics page: finance, inventory and the
audit log. Every figure here is derived from data other screens already
write - nothing is stored. Rows for the chosen period are aggregated in
Python (a temple's volume is thousands of rows, not millions), which keeps the
queries portable between Postgres and the SQLite test database.

Times: audit timestamps are stored in UTC; days and hours are reported in IST,
the temple's local time, so "off-hours" means night in Thorur.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.donation import Donation
from app.models.finance import ExpenseStatus, ExpenseTransaction, IncomeTransaction
from app.models.inventory import InventoryItem, ItemKind, MovementType, StockMovement

IST = timedelta(hours=5, minutes=30)
OFF_HOURS = (22, 6)  # 10 pm - 6 am IST
SENSITIVE_ACTIONS = ("DELETE", "DELETE_ACCOUNT", "VOID", "REJECT", "WRITE_OFF", "ADJUST", "LOGIN_FAILED",
                     "PASSWORD_CHANGE", "REVOKE", "SIGN_FAILED", "UPLOAD_SIGNATURE", "REMOVE_SIGNATURE", "UPLOAD_SEAL")


def _month(d) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def month_keys(months: int, today: date | None = None) -> List[str]:
    """The last `months` calendar months, oldest first, ending with this one."""
    today = today or date.today()
    y, m = today.year, today.month
    keys = []
    for _ in range(months):
        keys.append(f"{y:04d}-{m:02d}")
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return keys[::-1]


def _start_of(key: str) -> date:
    y, m = (int(x) for x in key.split("-"))
    return date(y, m, 1)


def _money(v) -> Decimal:
    return Decimal(v or 0).quantize(Decimal("0.01"))


def _is_off_hours(local: datetime) -> bool:
    late, early = OFF_HOURS
    return local.hour >= late or local.hour < early


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    # ---- finance -----------------------------------------------------------------------
    def finance(self, months: int) -> dict:
        keys = month_keys(months)
        start = _start_of(keys[0])
        prev_start = _start_of(month_keys(months * 2)[0])

        incomes = self.db.query(IncomeTransaction.received_at, IncomeTransaction.amount,
                                IncomeTransaction.source_type, IncomeTransaction.payment_mode) \
            .filter(IncomeTransaction.received_at >= datetime.combine(prev_start, datetime.min.time())).all()
        expenses = self.db.query(ExpenseTransaction.expense_date, ExpenseTransaction.amount,
                                 ExpenseTransaction.category, ExpenseTransaction.paid_to) \
            .filter(ExpenseTransaction.status == ExpenseStatus.APPROVED,
                    ExpenseTransaction.expense_date >= prev_start).all()

        series = {k: {"month": k, "income": Decimal(0), "expenses": Decimal(0)} for k in keys}
        by_source, by_mode, by_category = defaultdict(Decimal), defaultdict(lambda: [0, Decimal(0)]), defaultdict(Decimal)
        payees = defaultdict(lambda: [0, Decimal(0)])
        totals = {"income": Decimal(0), "expenses": Decimal(0)}
        previous = {"income": Decimal(0), "expenses": Decimal(0)}

        for when, amount, source, mode in incomes:
            amount = Decimal(amount)
            if when.date() < start:
                previous["income"] += amount
                continue
            series[_month(when)]["income"] += amount
            totals["income"] += amount
            by_source[source.value] += amount
            by_mode[mode.value][0] += 1
            by_mode[mode.value][1] += amount
        for when, amount, category, paid_to in expenses:
            amount = Decimal(amount)
            if when < start:
                previous["expenses"] += amount
                continue
            series[_month(when)]["expenses"] += amount
            totals["expenses"] += amount
            by_category[category.value] += amount
            payee = payees[paid_to.strip().title()]
            payee[0] += 1
            payee[1] += amount

        donations = self.db.query(func.count(Donation.id), func.sum(Donation.amount),
                                  func.count(func.distinct(Donation.donor_id))) \
            .filter(Donation.donated_on >= datetime.combine(start, datetime.min.time())).one()
        count, total, donors = donations[0] or 0, _money(donations[1]), donations[2] or 0

        return {
            "months": [{**v, "net": v["income"] - v["expenses"]} for v in series.values()],
            "totals": {**totals, "net": totals["income"] - totals["expenses"]},
            "previous": {**previous, "net": previous["income"] - previous["expenses"]},
            "income_by_source": _ranked(by_source),
            "expense_by_category": _ranked(by_category),
            "payment_modes": sorted(({"mode": k, "count": c, "amount": a} for k, (c, a) in by_mode.items()),
                                    key=lambda r: r["amount"], reverse=True),
            "top_payees": sorted(({"name": k, "count": c, "amount": a} for k, (c, a) in payees.items()),
                                 key=lambda r: r["amount"], reverse=True)[:10],
            "donations": {"count": count, "total": total, "donors": donors,
                          "average": _money(total / count) if count else Decimal(0)},
        }

    # ---- inventory -----------------------------------------------------------------------
    def inventory(self, months: int) -> dict:
        keys = month_keys(months)
        start = _start_of(keys[0])
        items = self.db.query(InventoryItem).filter(InventoryItem.is_active.is_(True)).all()
        stock_by_category = defaultdict(Decimal)
        for i in items:
            if i.kind == ItemKind.CONSUMABLE:
                stock_by_category[i.category] += Decimal(i.quantity) * Decimal(i.avg_unit_cost)

        moves = (self.db.query(StockMovement.movement_date, StockMovement.type, StockMovement.quantity,
                               StockMovement.total_value, InventoryItem.name, InventoryItem.unit)
                 .join(InventoryItem, InventoryItem.id == StockMovement.item_id)
                 .filter(StockMovement.movement_date >= start).all())
        consumption = {k: {"month": k, "used": Decimal(0), "written_off": Decimal(0), "donated_in": 0} for k in keys}
        used_items: Dict[Tuple[str, str], List] = defaultdict(lambda: [Decimal(0), Decimal(0)])
        for when, kind, qty, value, name, unit in moves:
            row = consumption[_month(when)]
            value = -Decimal(value or 0)
            if kind == MovementType.USAGE:
                row["used"] += value
                used_items[(name, unit)][0] += -Decimal(qty)
                used_items[(name, unit)][1] += value
            elif kind == MovementType.WRITE_OFF:
                row["written_off"] += value
            elif kind == MovementType.DONATION_IN:
                row["donated_in"] += 1

        return {
            "stock_by_category": _ranked({k: _money(v) for k, v in stock_by_category.items()}),
            "consumption": [{**v, "used": _money(v["used"]), "written_off": _money(v["written_off"])}
                            for v in consumption.values()],
            "top_used": sorted(({"item_name": n, "unit": u, "quantity": q, "value": _money(v)}
                                for (n, u), (q, v) in used_items.items()), key=lambda r: r["value"], reverse=True)[:10],
        }

    # ---- audit log -----------------------------------------------------------------------
    def audit(self, days: int) -> dict:
        today_local = (datetime.utcnow() + IST).date()
        start_local = today_local - timedelta(days=days - 1)
        since_utc = datetime.combine(start_local, datetime.min.time()) - IST
        rows = (self.db.query(AuditLog.id, AuditLog.created_at, AuditLog.actor_username, AuditLog.action,
                              AuditLog.entity_type, AuditLog.summary, AuditLog.ip_address)
                .filter(AuditLog.created_at >= since_utc).order_by(AuditLog.created_at.desc()).all())

        per_day = {start_local + timedelta(days=i): 0 for i in range(days)}
        by_hour = [0] * 24
        actors, actions, entities = Counter(), Counter(), Counter()
        actor_deletes, failed_by_ip = Counter(), Counter()
        off_hours = deletions = logins = failed = 0
        sensitive = []
        for row in rows:
            local = row.created_at + IST
            per_day[local.date()] = per_day.get(local.date(), 0) + 1
            by_hour[local.hour] += 1
            actions[row.action] += 1
            entities[row.entity_type] += 1
            is_off = _is_off_hours(local)
            if row.action == "LOGIN_FAILED":
                failed += 1
                failed_by_ip[row.ip_address or "unknown"] += 1
            else:
                actors[row.actor_username or "system"] += 1
            if row.action == "LOGIN":
                logins += 1
            if row.action in ("DELETE", "DELETE_ACCOUNT"):
                deletions += 1
                actor_deletes[row.actor_username or "system"] += 1
            if is_off and row.action != "LOGIN_FAILED":
                off_hours += 1
            if (row.action in SENSITIVE_ACTIONS or is_off) and len(sensitive) < 25:
                sensitive.append({"id": row.id, "created_at": row.created_at, "actor": row.actor_username,
                                  "action": row.action, "entity_type": row.entity_type, "summary": row.summary,
                                  "ip_address": row.ip_address, "off_hours": is_off})

        return {
            "days": days,
            "totals": {"events": len(rows), "active_users": len(actors), "logins": logins, "failed_logins": failed,
                       "deletions": deletions, "off_hours": off_hours},
            "per_day": [{"date": d, "count": c} for d, c in sorted(per_day.items()) if d >= start_local],
            "by_hour": by_hour,
            "by_actor": [{"name": n, "count": c, "deletions": actor_deletes.get(n, 0)}
                         for n, c in actors.most_common(10)],
            "by_action": [{"name": n, "count": c} for n, c in actions.most_common()],
            "by_entity": [{"name": n, "count": c} for n, c in entities.most_common(12)],
            "failed_login_ips": [{"name": ip, "count": c} for ip, c in failed_by_ip.most_common(5)],
            "sensitive": sensitive,
        }


def _ranked(values: Dict[str, Decimal]) -> List[dict]:
    return [{"name": k, "amount": v} for k, v in sorted(values.items(), key=lambda kv: kv[1], reverse=True) if v]
