from typing import List, Optional
from datetime import date, datetime, time
from sqlalchemy.orm import Session
from app.repositories.finance_repo import FinanceRepository
from app.schemas.finance import IncomeTransactionCreate, ExpenseTransactionCreate, FinanceSummary
from fastapi import HTTPException

class FinanceService:
    @staticmethod
    def add_income(db: Session, income_in: IncomeTransactionCreate, user_id: int):
        if income_in.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        income_data = income_in.model_dump()
        income_data["received_by"] = user_id
        return FinanceRepository.create_income(db, income_data)

    @staticmethod
    def add_expense(db: Session, expense_in: ExpenseTransactionCreate, user_id: int):
        if expense_in.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        expense_data = expense_in.model_dump()
        expense_data["approved_by"] = user_id
        return FinanceRepository.create_expense(db, expense_data)

    @staticmethod
    def get_summary(db: Session) -> FinanceSummary:
        total_income = FinanceRepository.get_total_income(db)
        total_expenses = FinanceRepository.get_total_expenses(db)
        
        income_groups = FinanceRepository.get_income_summary(db)
        expense_groups = FinanceRepository.get_expense_summary(db)
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
            "income_by_source": {source.value: amount for source, amount in income_groups},
            "expense_by_category": {cat.value: amount for cat, amount in expense_groups}
        }

    @staticmethod
    def get_ledger(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None):
        incomes = FinanceRepository.list_income(db, start_date, end_date)
        expenses = FinanceRepository.list_expenses(db, start_date, end_date)
        
        ledger = []
        for i in incomes:
            ledger.append({
                "id": str(i.id),
                "date": i.received_at,
                "type": "INCOME",
                "category_or_source": i.source_type.value,
                "description": f"Income from {i.source_type.value}",
                "amount": i.amount,
                "payment_mode": i.payment_mode.value
            })
            
        for e in expenses:
            ledger.append({
                "id": str(e.id),
                "date": e.expense_date,
                "type": "EXPENSE",
                "category_or_source": e.category.value,
                "description": e.description,
                "amount": -e.amount,
                "payment_mode": e.payment_mode.value
            })
            
        # Sort by date descending. Incomes carry a datetime (received_at) but
        # expenses only a date (expense_date); comparing the two raised
        # "TypeError: can't compare datetime.datetime to datetime.date", so the
        # ledger endpoint returned HTTP 500 as soon as both kinds existed.
        def sort_key(entry):
            d = entry["date"]
            return d if isinstance(d, datetime) else datetime.combine(d, time.min)

        ledger.sort(key=sort_key, reverse=True)
        return ledger
