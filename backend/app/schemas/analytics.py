from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.common import MoneyOut


class NamedAmount(BaseModel):
    name: str
    amount: MoneyOut


class NamedCount(BaseModel):
    name: str
    count: int


# ---- finance --------------------------------------------------------------------------
class FinanceMonth(BaseModel):
    month: str  # YYYY-MM
    income: MoneyOut
    expenses: MoneyOut
    net: MoneyOut


class FinanceTotals(BaseModel):
    income: MoneyOut
    expenses: MoneyOut
    net: MoneyOut


class PaymentModeLine(BaseModel):
    mode: str
    count: int
    amount: MoneyOut


class PayeeLine(BaseModel):
    name: str
    count: int
    amount: MoneyOut


class DonationStats(BaseModel):
    count: int
    total: MoneyOut
    donors: int
    average: MoneyOut


class FinanceAnalytics(BaseModel):
    months: List[FinanceMonth]
    totals: FinanceTotals
    previous: FinanceTotals  # the same length of time just before, for comparison
    income_by_source: List[NamedAmount]
    expense_by_category: List[NamedAmount]
    payment_modes: List[PaymentModeLine]
    top_payees: List[PayeeLine]
    donations: DonationStats


# ---- inventory ------------------------------------------------------------------------
class ConsumptionMonth(BaseModel):
    month: str
    used: MoneyOut
    written_off: MoneyOut
    donated_in: int


class UsedItem(BaseModel):
    item_name: str
    unit: str
    quantity: Decimal
    value: MoneyOut


class InventoryAnalytics(BaseModel):
    stock_by_category: List[NamedAmount]
    consumption: List[ConsumptionMonth]
    top_used: List[UsedItem]


# ---- audit log ------------------------------------------------------------------------
class AuditTotals(BaseModel):
    events: int
    active_users: int
    logins: int
    failed_logins: int
    deletions: int
    off_hours: int


class AuditDay(BaseModel):
    date: date
    count: int


class ActorLine(BaseModel):
    name: str
    count: int
    deletions: int


class SensitiveEvent(BaseModel):
    id: int
    created_at: datetime
    actor: Optional[str] = None
    action: str
    entity_type: str
    summary: Optional[str] = None
    ip_address: Optional[str] = None
    off_hours: bool


class AuditAnalytics(BaseModel):
    days: int
    totals: AuditTotals
    per_day: List[AuditDay]
    by_hour: List[int]  # 24 counts, IST hour of day
    by_actor: List[ActorLine]
    by_action: List[NamedCount]
    by_entity: List[NamedCount]
    failed_login_ips: List[NamedCount]
    sensitive: List[SensitiveEvent]
