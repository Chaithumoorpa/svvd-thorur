from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.finance import IncomeTransaction, ExpenseTransaction, IncomeSourceType, ExpenseCategory
from uuid import UUID

class FinanceRepository:
    @staticmethod
    def create_income(db: Session, income_data: dict) -> IncomeTransaction:
        db_income = IncomeTransaction(**income_data)
        db.add(db_income)
        db.commit()
        db.refresh(db_income)
        return db_income

    @staticmethod
    def create_expense(db: Session, expense_data: dict) -> ExpenseTransaction:
        db_expense = ExpenseTransaction(**expense_data)
        db.add(db_expense)
        db.commit()
        db.refresh(db_expense)
        return db_expense

    @staticmethod
    def list_income(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        source_type: Optional[IncomeSourceType] = None
    ) -> List[IncomeTransaction]:
        query = db.query(IncomeTransaction)
        if start_date:
            query = query.filter(IncomeTransaction.received_at >= start_date)
        if end_date:
            query = query.filter(IncomeTransaction.received_at <= end_date)
        if source_type:
            query = query.filter(IncomeTransaction.source_type == source_type)
        return query.order_by(IncomeTransaction.received_at.desc()).all()

    @staticmethod
    def list_expenses(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[ExpenseCategory] = None
    ) -> List[ExpenseTransaction]:
        query = db.query(ExpenseTransaction)
        if start_date:
            query = query.filter(ExpenseTransaction.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseTransaction.expense_date <= end_date)
        if category:
            query = query.filter(ExpenseTransaction.category == category)
        return query.order_by(ExpenseTransaction.expense_date.desc()).all()

    @staticmethod
    def get_income_summary(db: Session):
        return db.query(
            IncomeTransaction.source_type,
            func.sum(IncomeTransaction.amount)
        ).group_by(IncomeTransaction.source_type).all()

    @staticmethod
    def get_expense_summary(db: Session):
        return db.query(
            ExpenseTransaction.category,
            func.sum(ExpenseTransaction.amount)
        ).group_by(ExpenseTransaction.category).all()

    @staticmethod
    def get_total_income(db: Session, before_date: Optional[date] = None) -> int:
        query = db.query(func.sum(IncomeTransaction.amount))
        if before_date:
            query = query.filter(IncomeTransaction.received_at < before_date)
        return query.scalar() or 0

    @staticmethod
    def get_total_expenses(db: Session, before_date: Optional[date] = None) -> int:
        query = db.query(func.sum(ExpenseTransaction.amount))
        if before_date:
            query = query.filter(ExpenseTransaction.expense_date < before_date)
        return query.scalar() or 0
