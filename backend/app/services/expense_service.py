"""Expenses: entry, approval, correction, voiding, bills and monthly budgets.

Life of an expense:
  admin enters it          -> APPROVED (counted at once, as before this workflow)
  staff submits it         -> PENDING  -> approved / rejected by an admin
  APPROVED, found wrong    -> corrected (reason + old/new values in the audit log)
                              or VOID (reason kept; it stops counting)
Only APPROVED expenses count anywhere money is totalled (see finance_repo).
"""
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.core.pagination import PageParams
from app.models.festival import Festival
from app.models.finance import ExpenseBudget, ExpenseCategory, ExpenseStatus, ExpenseTransaction
from app.models.inventory import StockMovement
from app.models.user import User
from app.schemas.finance import (
    EXPENSE_BILL_PREFIX, BudgetLine, BudgetStatus, BudgetStatusLine, ExpenseListItem, ExpenseTransactionCreate,
    ExpenseUpdate,
)
from app.services.storage_service import StorageService

_EDITABLE = ("category", "description", "amount", "payment_mode", "paid_to", "expense_date", "notes",
             "bill_key", "festival_id")
_BILL_TYPES = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif",
               "pdf": "application/pdf"}


def month_bounds(month: str) -> Tuple[date, date]:
    """'2026-10' -> (2026-10-01, 2026-10-31)."""
    try:
        year, mon = (int(x) for x in month.split("-"))
        first = date(year, mon, 1)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="Month must look like 2026-10")
    return first, date(year, mon, monthrange(year, mon)[1])


def _plain(value):
    """JSON-safe value for an audit log diff."""
    if isinstance(value, (Decimal, date, datetime, UUID)):
        return str(value)
    return getattr(value, "value", value)


class ExpenseService:
    def __init__(self, db: Session, storage: Optional[StorageService] = None):
        self.db = db
        self.storage = storage or StorageService()

    # ---- create ----------------------------------------------------------------------
    def build(self, data: ExpenseTransactionCreate, user: User, can_approve: bool) -> ExpenseTransaction:
        """A new expense added to the session but not committed (an inventory
        purchase commits it together with its stock movement)."""
        self._check_festival(data.festival_id)
        now = datetime.utcnow()
        row = ExpenseTransaction(
            **data.model_dump(),
            status=ExpenseStatus.APPROVED if can_approve else ExpenseStatus.PENDING,
            submitted_by=user.id,
            approved_by=user.id if can_approve else None,
            decided_at=now if can_approve else None,
        )
        self.db.add(row)
        return row

    def create(self, data: ExpenseTransactionCreate, user: User, can_approve: bool) -> ExpenseTransaction:
        row = self.build(data, user, can_approve)
        self.db.commit()
        self.db.refresh(row)
        return row

    # ---- read ------------------------------------------------------------------------
    def get(self, expense_id: UUID) -> ExpenseTransaction:
        row = self.db.get(ExpenseTransaction, expense_id)
        if not row:
            raise HTTPException(status_code=404, detail="Expense not found")
        return row

    def list(self, params: PageParams, *, status: Optional[ExpenseStatus] = None,
             category: Optional[ExpenseCategory] = None, start: Optional[date] = None, end: Optional[date] = None,
             festival_id: Optional[int] = None, submitted_by: Optional[int] = None,
             search: Optional[str] = None) -> Tuple[List[ExpenseListItem], int]:
        submitter, approver = aliased(User), aliased(User)
        query = (
            self.db.query(ExpenseTransaction, submitter.username, approver.username, Festival.name,
                          StockMovement.item_id)
            .outerjoin(submitter, submitter.id == ExpenseTransaction.submitted_by)
            .outerjoin(approver, approver.id == ExpenseTransaction.approved_by)
            .outerjoin(Festival, Festival.id == ExpenseTransaction.festival_id)
            .outerjoin(StockMovement, StockMovement.expense_id == ExpenseTransaction.id)
        )
        if status:
            query = query.filter(ExpenseTransaction.status == status)
        if category:
            query = query.filter(ExpenseTransaction.category == category)
        if start:
            query = query.filter(ExpenseTransaction.expense_date >= start)
        if end:
            query = query.filter(ExpenseTransaction.expense_date <= end)
        if festival_id:
            query = query.filter(ExpenseTransaction.festival_id == festival_id)
        if submitted_by:
            query = query.filter(ExpenseTransaction.submitted_by == submitted_by)
        if search:
            like = f"%{search.strip()}%"
            query = query.filter(ExpenseTransaction.description.ilike(like) | ExpenseTransaction.paid_to.ilike(like))

        total = query.order_by(None).count()
        rows = (query.order_by(ExpenseTransaction.expense_date.desc(), ExpenseTransaction.created_at.desc(),
                               ExpenseTransaction.id.desc())
                .offset(params.offset).limit(params.page_size).all())
        items = []
        for expense, submitted_name, approved_name, festival_name, item_id in rows:
            out = ExpenseListItem.model_validate(expense)
            out.submitted_by_name, out.approved_by_name = submitted_name, approved_name
            out.festival_name, out.inventory_item_id = festival_name, item_id
            items.append(out)
        return items, total

    def pending_count(self) -> int:
        return self.db.query(func.count(ExpenseTransaction.id)) \
            .filter(ExpenseTransaction.status == ExpenseStatus.PENDING).scalar() or 0

    # ---- change ----------------------------------------------------------------------
    def update(self, expense_id: UUID, data: ExpenseUpdate, user: User, is_approver: bool) -> Tuple[ExpenseTransaction, Dict]:
        row = self.get(expense_id)
        if row.status == ExpenseStatus.PENDING:
            if not is_approver and row.submitted_by != user.id:
                raise HTTPException(status_code=403, detail="You can only change expenses you submitted")
        elif row.status == ExpenseStatus.APPROVED:
            if not is_approver:
                raise HTTPException(status_code=403, detail="Only an admin can correct an approved expense")
            if not data.reason:
                raise HTTPException(status_code=422, detail="Give a reason for correcting an approved expense")
        else:
            raise HTTPException(status_code=409, detail=f"A {row.status.value.lower()} expense can't be changed")

        fields = data.model_dump(exclude_unset=True, exclude={"reason"})
        if "festival_id" in fields:
            self._check_festival(fields["festival_id"])
        changes = {}
        for key in _EDITABLE:
            if key in fields and fields[key] != getattr(row, key):
                if key in ("category", "description", "amount", "payment_mode", "paid_to", "expense_date") \
                        and fields[key] is None:
                    raise HTTPException(status_code=422, detail=f"{key.replace('_', ' ').capitalize()} is required")
                changes[key] = {"from": _plain(getattr(row, key)), "to": _plain(fields[key])}
                setattr(row, key, fields[key])
        if changes:
            if data.reason:
                changes["reason"] = data.reason
            self.db.commit()
            self.db.refresh(row)
        return row, changes

    def approve(self, expense_id: UUID, user: User) -> ExpenseTransaction:
        row = self._pending(expense_id)
        row.status, row.approved_by, row.decided_at = ExpenseStatus.APPROVED, user.id, datetime.utcnow()
        self.db.commit()
        self.db.refresh(row)
        return row

    def reject(self, expense_id: UUID, user: User, reason: str) -> ExpenseTransaction:
        row = self._pending(expense_id)
        row.status, row.approved_by, row.decided_at = ExpenseStatus.REJECTED, user.id, datetime.utcnow()
        row.rejection_reason = reason
        self.db.commit()
        self.db.refresh(row)
        return row

    def void(self, expense_id: UUID, user: User, reason: str) -> ExpenseTransaction:
        row = self.get(expense_id)
        if row.status not in (ExpenseStatus.APPROVED, ExpenseStatus.PENDING):
            raise HTTPException(status_code=409, detail=f"A {row.status.value.lower()} expense can't be voided")
        row.status, row.voided_by, row.voided_at, row.void_reason = (
            ExpenseStatus.VOID, user.id, datetime.utcnow(), reason)
        self.db.commit()
        self.db.refresh(row)
        return row

    # ---- bills -----------------------------------------------------------------------
    def bill_upload(self, content_type: str) -> dict:
        return self.storage.create_upload(content_type, key_prefix=EXPENSE_BILL_PREFIX, allow_pdf=True)

    def bill_link(self, expense_id: UUID) -> dict:
        row = self.get(expense_id)
        if not row.bill_key:
            raise HTTPException(status_code=404, detail="No bill is attached to this expense")
        if not self.storage.enabled:
            raise HTTPException(status_code=503, detail="File storage is not configured")
        ext = row.bill_key.rsplit(".", 1)[-1]
        return {"url": self.storage.presigned_get(row.bill_key, expires_in=300),
                "content_type": _BILL_TYPES.get(ext, "application/octet-stream")}

    # ---- budgets ---------------------------------------------------------------------
    def budget_status(self, month: str) -> BudgetStatus:
        first, last = month_bounds(month)
        budgets = {b.category: Decimal(b.amount) for b in
                   self.db.query(ExpenseBudget).filter(ExpenseBudget.month == first)}
        sums = dict(
            ((cat, st), Decimal(total or 0)) for cat, st, total in
            self.db.query(ExpenseTransaction.category, ExpenseTransaction.status, func.sum(ExpenseTransaction.amount))
            .filter(ExpenseTransaction.expense_date >= first, ExpenseTransaction.expense_date <= last,
                    ExpenseTransaction.status.in_((ExpenseStatus.APPROVED, ExpenseStatus.PENDING)))
            .group_by(ExpenseTransaction.category, ExpenseTransaction.status)
        )
        lines = []
        for cat in ExpenseCategory:
            spent = sums.get((cat, ExpenseStatus.APPROVED), Decimal(0))
            pending = sums.get((cat, ExpenseStatus.PENDING), Decimal(0))
            budget = budgets.get(cat)
            if budget is None and not spent and not pending:
                continue
            lines.append(BudgetStatusLine(
                category=cat, budget=budget, spent=spent, pending=pending,
                remaining=(budget - spent) if budget is not None else None,
                percent_used=round(float(spent / budget * 100), 1) if budget else None,
                over_budget=budget is not None and spent > budget,
            ))
        return BudgetStatus(
            month=first.strftime("%Y-%m"), lines=lines,
            total_budget=sum(budgets.values(), Decimal(0)),
            total_spent=sum((l.spent for l in lines), Decimal(0)),
            total_pending=sum((l.pending for l in lines), Decimal(0)),
        )

    def set_budgets(self, month: str, lines: List[BudgetLine], user: User) -> Dict[str, str]:
        """Upsert this month's budgets; an amount of 0 removes that category's budget."""
        first, _ = month_bounds(month)
        existing = {b.category: b for b in self.db.query(ExpenseBudget).filter(ExpenseBudget.month == first)}
        changed = {}
        for line in lines:
            row = existing.get(line.category)
            if line.amount == 0:
                if row:
                    self.db.delete(row)
                    changed[line.category.value] = "removed"
                continue
            if row:
                if Decimal(row.amount) != line.amount:
                    row.amount, row.updated_by = line.amount, user.id
                    changed[line.category.value] = str(line.amount)
            else:
                self.db.add(ExpenseBudget(month=first, category=line.category, amount=line.amount, updated_by=user.id))
                changed[line.category.value] = str(line.amount)
        self.db.commit()
        return changed

    def copy_budgets(self, from_month: str, to_month: str, user: User) -> int:
        """Start a month from another month's budgets (replacing any already set)."""
        source, _ = month_bounds(from_month)
        target, _ = month_bounds(to_month)
        rows = self.db.query(ExpenseBudget).filter(ExpenseBudget.month == source).all()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No budgets were set for {from_month}")
        self.db.query(ExpenseBudget).filter(ExpenseBudget.month == target).delete()
        for b in rows:
            self.db.add(ExpenseBudget(month=target, category=b.category, amount=b.amount, updated_by=user.id))
        self.db.commit()
        return len(rows)

    # ---- helpers ---------------------------------------------------------------------
    def _pending(self, expense_id: UUID) -> ExpenseTransaction:
        row = self.get(expense_id)
        if row.status != ExpenseStatus.PENDING:
            raise HTTPException(status_code=409, detail=f"This expense is already {row.status.value.lower()}")
        return row

    def _check_festival(self, festival_id: Optional[int]) -> None:
        if festival_id and not self.db.get(Festival, festival_id):
            raise HTTPException(status_code=422, detail="That festival doesn't exist")
