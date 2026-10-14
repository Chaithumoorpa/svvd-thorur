from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.finance import ExpenseCategory, ExpenseStatus, IncomeSourceType, PaymentMode
from app.schemas.common import MoneyIn, MoneyInOrZero, MoneyOut, blank_to_none

# Bills are stored privately under receipts/ - the prefix the server's IAM role
# can already write and read (see StorageService.upload_private).
EXPENSE_BILL_PREFIX = "receipts/expense-bills"
BillKey = Annotated[str, StringConstraints(pattern=rf"^{EXPENSE_BILL_PREFIX}/[0-9a-f]{{32}}\.(jpg|png|webp|gif|pdf)$")]
Text255 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]


class IncomeTransactionCreate(BaseModel):
    # SEVA and DONATION are recorded automatically (seva ticket booking /
    # donation entry) - allowing them here would let a manual entry pose as
    # one, double-counting or bypassing the actual ticket/donation record.
    # HUNDI has no other originating record, so it stays manual-only.
    source_type: Annotated[IncomeSourceType, Field()]
    amount: MoneyIn
    payment_mode: PaymentMode
    reference_id: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("source_type")
    @classmethod
    def _manual_source_only(cls, v: IncomeSourceType) -> IncomeSourceType:
        if v not in (IncomeSourceType.MANUAL, IncomeSourceType.HUNDI):
            raise ValueError(
                "Only MANUAL or HUNDI income can be entered directly - "
                "SEVA and DONATION income is recorded automatically"
            )
        return v

    @field_validator("reference_id", "notes", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class IncomeTransactionOut(BaseModel):
    id: UUID
    source_type: IncomeSourceType
    amount: MoneyOut
    payment_mode: PaymentMode
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    received_by: Optional[int] = None  # None: collected automatically online, not by staff
    received_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExpenseTransactionCreate(BaseModel):
    category: ExpenseCategory
    description: Text255
    amount: MoneyIn
    payment_mode: PaymentMode
    paid_to: Text255
    expense_date: date
    notes: Optional[str] = Field(default=None, max_length=2000)
    bill_key: Optional[BillKey] = None
    festival_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("notes", "bill_key", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("expense_date")
    @classmethod
    def _not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("The expense date can't be in the future")
        return v


class ExpenseUpdate(BaseModel):
    """A correction. Changing an already-approved expense needs a reason,
    which goes into the audit log together with the old and new values."""
    category: Optional[ExpenseCategory] = None
    description: Optional[Text255] = None
    amount: Optional[MoneyIn] = None
    payment_mode: Optional[PaymentMode] = None
    paid_to: Optional[Text255] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    bill_key: Optional[BillKey] = None
    festival_id: Optional[int] = Field(default=None, ge=1)
    reason: Optional[Reason] = None

    @field_validator("notes", "bill_key", "reason", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("expense_date")
    @classmethod
    def _not_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError("The expense date can't be in the future")
        return v


class ExpenseReason(BaseModel):
    reason: Reason


class ExpenseTransactionOut(BaseModel):
    id: UUID
    category: ExpenseCategory
    description: str
    amount: MoneyOut
    payment_mode: PaymentMode
    paid_to: str
    expense_date: date
    notes: Optional[str] = None
    status: ExpenseStatus
    submitted_by: Optional[int] = None
    approved_by: Optional[int] = None
    decided_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    voided_by: Optional[int] = None
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    has_bill: bool = False
    festival_id: Optional[int] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ExpenseListItem(ExpenseTransactionOut):
    """An expense with the names a reviewer needs (no extra lookups in the UI)."""
    submitted_by_name: Optional[str] = None
    approved_by_name: Optional[str] = None
    festival_name: Optional[str] = None
    # Set when the expense was created by an inventory purchase
    inventory_item_id: Optional[int] = None


class BillLink(BaseModel):
    url: str
    content_type: str


class BudgetLine(BaseModel):
    category: ExpenseCategory
    amount: MoneyInOrZero


class BudgetSet(BaseModel):
    lines: List[BudgetLine] = Field(max_length=len(ExpenseCategory))


class BudgetStatusLine(BaseModel):
    category: ExpenseCategory
    budget: Optional[MoneyOut] = None
    spent: MoneyOut          # approved expenses in the month
    pending: MoneyOut        # submitted, awaiting approval
    remaining: Optional[MoneyOut] = None
    percent_used: Optional[float] = None
    over_budget: bool = False


class BudgetStatus(BaseModel):
    month: str  # YYYY-MM
    lines: List[BudgetStatusLine]
    total_budget: MoneyOut
    total_spent: MoneyOut
    total_pending: MoneyOut


class FinanceSummary(BaseModel):
    total_income: MoneyOut
    total_expenses: MoneyOut
    balance: MoneyOut
    income_by_source: Dict[str, MoneyOut]
    expense_by_category: Dict[str, MoneyOut]


class LedgerEntry(BaseModel):
    id: str
    date: datetime
    type: str  # "INCOME" or "EXPENSE"
    category_or_source: str
    description: str
    amount: MoneyOut  # signed: income positive, expense negative
    payment_mode: str
