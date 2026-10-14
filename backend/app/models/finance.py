import enum
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Date, Numeric, UniqueConstraint
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
    # Paid through the Razorpay checkout (card/UPI/netbanking/wallet - the specific
    # instrument is recorded in the transaction notes, not broken out here).
    ONLINE = "ONLINE"

class ExpenseCategory(str, enum.Enum):
    SALARY = "SALARY"
    MATERIAL = "MATERIAL"
    MAINTENANCE = "MAINTENANCE"
    FESTIVAL = "FESTIVAL"
    OTHER = "OTHER"
    POOJA_SUPPLIES = "POOJA_SUPPLIES"  # ghee, oil, camphor, flowers, kumkum...
    ANNADANAM = "ANNADANAM"            # prasadam / free-meal provisions
    UTILITIES = "UTILITIES"            # electricity, water, phone, internet
    CONSTRUCTION = "CONSTRUCTION"      # building works, repairs beyond routine maintenance
    ASSETS = "ASSETS"                  # vessels, ornaments, furniture, equipment


class ExpenseStatus(str, enum.Enum):
    """Only APPROVED expenses count anywhere money is totalled (summary,
    ledger, reports, budgets). Expenses an admin enters are approved on entry;
    ones staff submit wait for an admin."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    VOID = "VOID"

class IncomeTransaction(Base):
    __tablename__ = "income_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(Enum(IncomeSourceType), nullable=False, index=True)
    # "donation:<id>" / "seva_ticket:<id>" / ... - looked up whenever the linked
    # record is edited or deleted, to keep the ledger in sync.
    reference_id = Column(String(255), nullable=True, index=True)
    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    payment_mode = Column(Enum(PaymentMode), nullable=False, index=True)
    # NULL for a payment nobody on staff handled - collected automatically
    # through the online (Razorpay) gateway, not received in person.
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
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
    expense_date = Column(Date, default=func.current_date(), nullable=False)
    notes = Column(Text, nullable=True)

    status = Column(Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.APPROVED,
                    server_default=ExpenseStatus.APPROVED.value, index=True)
    submitted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)     # approved / rejected at
    rejection_reason = Column(String(500), nullable=True)
    voided_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    voided_at = Column(DateTime, nullable=True)
    void_reason = Column(String(500), nullable=True)
    # Private S3 key of the bill / receipt photo or PDF (receipts/expense-bills/...)
    bill_key = Column(String(255), nullable=True)
    # Lets a festival's full cost be totalled (with the stock it used)
    festival_id = Column(Integer, ForeignKey("festivals.id", ondelete="SET NULL"), nullable=True, index=True)
    # created_at / updated_at come from Base, like every table


    @property
    def has_bill(self) -> bool:
        return bool(self.bill_key)


class ExpenseBudget(Base):
    """Monthly spending limit for one expense category."""
    __tablename__ = "expense_budgets"
    __table_args__ = (UniqueConstraint("month", "category", name="uq_expense_budget_month_category"),)

    id = Column(Integer, primary_key=True)
    month = Column(Date, nullable=False, index=True)  # always the 1st of the month
    category = Column(Enum(ExpenseCategory), nullable=False)
    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
