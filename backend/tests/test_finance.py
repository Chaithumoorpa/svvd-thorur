import pytest
from datetime import date
from sqlalchemy.orm import Session
from app.models.finance import IncomeSourceType, PaymentMode, ExpenseCategory
from app.services.finance_service import FinanceService
from app.schemas.finance import IncomeTransactionCreate, ExpenseTransactionCreate

def test_add_income(db: Session):
    # Setup: Create a user for received_by
    from app.models.user import User
    user = User(username="admin_finance", hashed_password="pw", roles=["ADMIN"])
    db.add(user)
    db.commit()
    db.refresh(user)

    income_in = IncomeTransactionCreate(
        source_type=IncomeSourceType.DONATION,
        amount=5000,
        payment_mode=PaymentMode.UPI,
        notes="General Donation"
    )
    
    income = FinanceService.add_income(db, income_in, user.id)
    assert income.amount == 5000
    assert income.source_type == IncomeSourceType.DONATION
    assert income.received_by == user.id

def test_add_expense_and_summary(db: Session):
    # Setup: Use existing user
    from app.models.user import User
    user = db.query(User).filter(User.username == "admin_finance").first()

    # Add Income
    FinanceService.add_income(db, IncomeTransactionCreate(
        source_type=IncomeSourceType.HUNDI,
        amount=10000,
        payment_mode=PaymentMode.CASH
    ), user.id)

    # Add Expense
    expense_in = ExpenseTransactionCreate(
        category=ExpenseCategory.MAINTENANCE,
        description="Electric Bill",
        amount=2000,
        payment_mode=PaymentMode.BANK,
        paid_to="Power Board",
        expense_date=date.today()
    )
    
    FinanceService.add_expense(db, expense_in, user.id)
    
    summary = FinanceService.get_summary(db)
    assert summary["total_income"] == 15000 # 5000 from prev test + 10000
    assert summary["total_expenses"] == 2000
    assert summary["balance"] == 13000

def test_ledger_sorting(db: Session):
    from app.models.user import User
    user = db.query(User).filter(User.username == "admin_finance").first()
    
    ledger = FinanceService.get_ledger(db)
    # Check if descending by date (income at now, expense at today)
    assert len(ledger) >= 3
    assert ledger[0]["amount"] != 0
