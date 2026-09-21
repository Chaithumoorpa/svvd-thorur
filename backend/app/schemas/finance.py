from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.finance import ExpenseCategory, IncomeSourceType, PaymentMode
from app.schemas.common import MoneyIn, MoneyOut, blank_to_none


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
    received_by: int
    received_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExpenseTransactionCreate(BaseModel):
    category: ExpenseCategory
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
    amount: MoneyIn
    payment_mode: PaymentMode
    paid_to: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)]
    expense_date: date
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("notes", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class ExpenseTransactionOut(BaseModel):
    id: UUID
    category: ExpenseCategory
    description: str
    amount: MoneyOut
    payment_mode: PaymentMode
    paid_to: str
    expense_date: date
    notes: Optional[str] = None
    approved_by: int
    model_config = ConfigDict(from_attributes=True)


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
