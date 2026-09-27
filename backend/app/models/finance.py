import enum
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import Base
from app.models.types import MONEY_PRECISION, MONEY_SCALE

class IncomeSourceType(str, enum.Enum):
    SEVA = "SEVA"
    DONATION = "DONATION"
    HUNDI = "HUNDI"
    MANUAL = "MANUAL"
    # Only on ledger rows from the retired standalone Abhishekam booking - Abhishekam
    # is an ordinary seva (SEVA) now. Kept so those rows still load.
    ABHISHEKAM = "ABHISHEKAM"

class PaymentMode(str, enum.Enum):
    CASH = "CASH"
    UPI = "UPI"
    BANK = "BANK"
    CHEQUE = "CHEQUE"

class ExpenseCategory(str, enum.Enum):
    SALARY = "SALARY"
    MATERIAL = "MATERIAL"
    MAINTENANCE = "MAINTENANCE"
    FESTIVAL = "FESTIVAL"
    OTHER = "OTHER"

class IncomeTransaction(Base):
    __tablename__ = "income_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(Enum(IncomeSourceType), nullable=False, index=True)
    # "donation:<id>" / "seva_ticket:<id>" / ... - looked up whenever the linked
    # record is edited or deleted, to keep the ledger in sync.
    reference_id = Column(String(255), nullable=True, index=True)
    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    payment_mode = Column(Enum(PaymentMode), nullable=False, index=True)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    received_at = Column(DateTime, default=func.now(), nullable=False)
    notes = Column(Text, nullable=True)

class ExpenseTransaction(Base):
    __tablename__ = "expense_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(Enum(ExpenseCategory), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    payment_mode = Column(Enum(PaymentMode), nullable=False, index=True)
    paid_to = Column(String(255), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expense_date = Column(Date, default=func.current_date(), nullable=False)
    notes = Column(Text, nullable=True)
