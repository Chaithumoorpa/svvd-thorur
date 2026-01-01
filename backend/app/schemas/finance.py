from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional, List
from app.models.finance import IncomeSourceType, PaymentMode, ExpenseCategory

class IncomeTransactionBase(BaseModel):
    source_type: IncomeSourceType
    amount: int
    payment_mode: PaymentMode
    reference_id: Optional[str] = None
    notes: Optional[str] = None

class IncomeTransactionCreate(IncomeTransactionBase):
    pass

class IncomeTransactionOut(IncomeTransactionBase):
    id: UUID
    received_by: int
    received_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExpenseTransactionBase(BaseModel):
    category: ExpenseCategory
    description: str
    amount: int
    payment_mode: PaymentMode
    paid_to: str
    expense_date: date
    notes: Optional[str] = None

class ExpenseTransactionCreate(ExpenseTransactionBase):
    pass

class ExpenseTransactionOut(ExpenseTransactionBase):
    id: UUID
    approved_by: int
    model_config = ConfigDict(from_attributes=True)

class FinanceSummary(BaseModel):
    total_income: int
    total_expenses: int
    balance: int
    income_by_source: dict
    expense_by_category: dict

class LedgerEntry(BaseModel):
    id: UUID
    date: datetime
    type: str # "INCOME" or "EXPENSE"
    category_or_source: str
    description: str
    amount: int
    payment_mode: str
