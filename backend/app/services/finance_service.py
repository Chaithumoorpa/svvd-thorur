from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.pagination import PageParams
from app.repositories.finance_repo import FinanceRepository
from app.schemas.finance import ExpenseTransactionCreate, IncomeTransactionCreate


def _as_datetime(value) -> datetime:
    """Expenses only carry a date; place them at end of day so same-day incomes sort before them."""
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.max)


class FinanceService:
    @staticmethod
    def add_income(db: Session, income_in: IncomeTransactionCreate, user_id: int):
        data = income_in.model_dump()
        data["received_by"] = user_id
        return FinanceRepository.create_income(db, data)

    @staticmethod
    def add_expense(db: Session, expense_in: ExpenseTransactionCreate, user_id: int):
        data = expense_in.model_dump()
        data["approved_by"] = user_id
        return FinanceRepository.create_expense(db, data)

    @staticmethod
    def get_summary(db: Session) -> Dict:
        total_income = FinanceRepository.get_total_income(db)
        total_expenses = FinanceRepository.get_total_expenses(db)
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
            "income_by_source": {s.value: Decimal(a) for s, a in FinanceRepository.get_income_summary(db)},
            "expense_by_category": {c.value: Decimal(a) for c, a in FinanceRepository.get_expense_summary(db)},
        }

    @staticmethod
    def _entries(incomes, expenses) -> List[Dict]:
        entries = [{
            "id": str(i.id), "date": i.received_at, "type": "INCOME",
            "category_or_source": i.source_type.value,
            "description": i.notes or f"Income from {i.source_type.value}",
            "amount": Decimal(i.amount), "payment_mode": i.payment_mode.value,
        } for i in incomes]
        entries += [{
            "id": str(e.id), "date": _as_datetime(e.expense_date), "type": "EXPENSE",
            "category_or_source": e.category.value, "description": e.description,
            "amount": -Decimal(e.amount), "payment_mode": e.payment_mode.value,
        } for e in expenses]
        # newest first; the id makes ties deterministic
        entries.sort(key=lambda x: (x["date"], x["id"]), reverse=True)
        return entries

    @staticmethod
    def get_ledger_page(db: Session, start_date: Optional[date], end_date: Optional[date],
                        params: PageParams) -> Tuple[List[Dict], int]:
        """
        One page of the merged income/expense ledger. Only (offset + page_size) rows of each
        source are fetched, so memory stays bounded however large the tables grow.
        """
        window = params.offset + params.page_size
        income_q = FinanceRepository.income_query(db, start_date, end_date)
        expense_q = FinanceRepository.expense_query(db, start_date, end_date)
        total = income_q.order_by(None).count() + expense_q.order_by(None).count()
        entries = FinanceService._entries(income_q.limit(window).all(), expense_q.limit(window).all())
        return entries[params.offset:window], total

    @staticmethod
    def get_ledger(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None):
        """Unpaginated ledger (small ranges / tests)."""
        return FinanceService._entries(
            FinanceRepository.list_income(db, start_date, end_date),
            FinanceRepository.list_expenses(db, start_date, end_date),
        )
