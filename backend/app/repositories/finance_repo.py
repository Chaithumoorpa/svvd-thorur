from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.finance import (
    ExpenseCategory, ExpenseTransaction, IncomeSourceType, IncomeTransaction,
)


def _start(d: date) -> datetime:
    return datetime.combine(d, time.min)


def _end_exclusive(d: date) -> datetime:
    """Inclusive end date -> exclusive next-midnight boundary (so the whole last day counts)."""
    return datetime.combine(d + timedelta(days=1), time.min)


class FinanceRepository:
    # ---- writes ---------------------------------------------------------------------
    @staticmethod
    def create_income(db: Session, income_data: dict) -> IncomeTransaction:
        row = IncomeTransaction(**income_data)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    @staticmethod
    def create_expense(db: Session, expense_data: dict) -> ExpenseTransaction:
        row = ExpenseTransaction(**expense_data)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    # ---- filtered queries (deterministic order: newest first, id as tie-breaker) --------
    @staticmethod
    def income_query(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None,
                     source_type: Optional[IncomeSourceType] = None):
        query = db.query(IncomeTransaction)
        if start_date:
            query = query.filter(IncomeTransaction.received_at >= _start(start_date))
        if end_date:
            query = query.filter(IncomeTransaction.received_at < _end_exclusive(end_date))
        if source_type:
            query = query.filter(IncomeTransaction.source_type == source_type)
        return query.order_by(IncomeTransaction.received_at.desc(), IncomeTransaction.id.desc())

    @staticmethod
    def expense_query(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None,
                      category: Optional[ExpenseCategory] = None):
        query = db.query(ExpenseTransaction)
        if start_date:
            query = query.filter(ExpenseTransaction.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseTransaction.expense_date <= end_date)
        if category:
            query = query.filter(ExpenseTransaction.category == category)
        return query.order_by(ExpenseTransaction.expense_date.desc(), ExpenseTransaction.id.desc())

    @staticmethod
    def list_income(db: Session, start_date=None, end_date=None, source_type=None) -> List[IncomeTransaction]:
        return FinanceRepository.income_query(db, start_date, end_date, source_type).all()

    @staticmethod
    def list_expenses(db: Session, start_date=None, end_date=None, category=None) -> List[ExpenseTransaction]:
        return FinanceRepository.expense_query(db, start_date, end_date, category).all()

    # ---- aggregates (done in SQL, never by loading every row) ------------------------------
    @staticmethod
    def get_income_summary(db: Session):
        return db.query(IncomeTransaction.source_type, func.sum(IncomeTransaction.amount)) \
            .group_by(IncomeTransaction.source_type).order_by(IncomeTransaction.source_type).all()

    @staticmethod
    def get_expense_summary(db: Session):
        return db.query(ExpenseTransaction.category, func.sum(ExpenseTransaction.amount)) \
            .group_by(ExpenseTransaction.category).order_by(ExpenseTransaction.category).all()

    @staticmethod
    def get_total_income(db: Session, before_date: Optional[date] = None) -> Decimal:
        query = db.query(func.sum(IncomeTransaction.amount))
        if before_date:
            query = query.filter(IncomeTransaction.received_at < _start(before_date))
        return Decimal(query.scalar() or 0)

    @staticmethod
    def get_total_expenses(db: Session, before_date: Optional[date] = None) -> Decimal:
        query = db.query(func.sum(ExpenseTransaction.amount))
        if before_date:
            query = query.filter(ExpenseTransaction.expense_date < before_date)
        return Decimal(query.scalar() or 0)
