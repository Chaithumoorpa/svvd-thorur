"""Expenses (submit / approve / reject / correct / void, bills) and monthly budgets.
Mounted under /finance."""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, page_params, set_total
from app.core.rbac import Permission, has_permission
from app.models.finance import ExpenseCategory, ExpenseStatus
from app.models.user import User
from app.schemas.finance import (
    BillLink, BudgetSet, BudgetStatus, ExpenseListItem, ExpenseReason, ExpenseTransactionCreate,
    ExpenseTransactionOut, ExpenseUpdate,
)
from app.schemas.upload import UploadUrlRequest, UploadUrlResponse
from app.services.expense_service import ExpenseService
from app.utils.dependencies import AuditContext, get_audit, get_db, require_any_permission, require_permission

router = APIRouter()

_submit = require_any_permission(Permission.EXPENSES_SUBMIT, Permission.FINANCE_WRITE)
_see = require_any_permission(Permission.EXPENSES_SUBMIT, Permission.FINANCE_READ)
_approve = require_permission(Permission.FINANCE_WRITE)
_read = require_permission(Permission.FINANCE_READ)


def get_expense_service(db: Session = Depends(get_db)) -> ExpenseService:
    return ExpenseService(db)


def _approver(user: User) -> bool:
    return has_permission(user.roles, Permission.FINANCE_WRITE)


def _sees_all(user: User) -> bool:
    return has_permission(user.roles, Permission.FINANCE_READ)


def _log_summary(row) -> str:
    return f"Rs. {row.amount} - {row.description} ({row.category.value})"


@router.post("/expenses", response_model=ExpenseTransactionOut, status_code=201)
def create_expense(payload: ExpenseTransactionCreate, service: ExpenseService = Depends(get_expense_service),
                   audit: AuditContext = Depends(get_audit), user: User = Depends(_submit)):
    """An admin's expense is approved on entry; anyone else's waits for an admin."""
    row = service.create(payload, user, can_approve=_approver(user))
    verb = "Recorded" if row.status == ExpenseStatus.APPROVED else "Submitted for approval"
    audit.log("CREATE", "expense", row.id, f"{verb}: expense {_log_summary(row)}",
              {"amount": row.amount, "category": row.category, "paid_to": row.paid_to, "status": row.status})
    return row


@router.get("/expenses", response_model=List[ExpenseListItem])
def list_expenses(
    response: Response,
    status: Optional[ExpenseStatus] = None,
    category: Optional[ExpenseCategory] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    festival_id: Optional[int] = None,
    mine: bool = False,
    q: Optional[str] = Query(None, max_length=100),
    params: PageParams = Depends(page_params),
    service: ExpenseService = Depends(get_expense_service),
    user: User = Depends(_see),
):
    """Newest first; total in X-Total-Count. Staff without finance access see only their own."""
    items, total = service.list(
        params, status=status, category=category, start=start_date, end=end_date, festival_id=festival_id,
        submitted_by=user.id if (mine or not _sees_all(user)) else None, search=q,
    )
    set_total(response, total)
    return items


@router.post("/expenses/bill-upload-url", response_model=UploadUrlResponse)
def bill_upload_url(payload: UploadUrlRequest, service: ExpenseService = Depends(get_expense_service),
                    _: User = Depends(_submit)):
    """Presigned upload for a bill photo or PDF - stored privately, viewed via /expenses/{id}/bill."""
    return service.bill_upload(payload.content_type)


@router.get("/expenses/{expense_id}/bill", response_model=BillLink)
def bill_link(expense_id: UUID, service: ExpenseService = Depends(get_expense_service), user: User = Depends(_see)):
    """A 5-minute private link to the bill."""
    if not _sees_all(user) and service.get(expense_id).submitted_by != user.id:
        raise HTTPException(status_code=403, detail="You can only view bills you submitted")
    return service.bill_link(expense_id)


@router.patch("/expenses/{expense_id}", response_model=ExpenseTransactionOut)
def update_expense(expense_id: UUID, payload: ExpenseUpdate, service: ExpenseService = Depends(get_expense_service),
                   audit: AuditContext = Depends(get_audit), user: User = Depends(_submit)):
    row, changes = service.update(expense_id, payload, user, is_approver=_approver(user))
    if changes:
        audit.log("UPDATE", "expense", row.id, f"Corrected expense {_log_summary(row)}", changes)
    return row


@router.post("/expenses/{expense_id}/approve", response_model=ExpenseTransactionOut)
def approve_expense(expense_id: UUID, service: ExpenseService = Depends(get_expense_service),
                    audit: AuditContext = Depends(get_audit), user: User = Depends(_approve)):
    row = service.approve(expense_id, user)
    audit.log("APPROVE", "expense", row.id, f"Approved expense {_log_summary(row)}", {"amount": row.amount})
    return row


@router.post("/expenses/{expense_id}/reject", response_model=ExpenseTransactionOut)
def reject_expense(expense_id: UUID, payload: ExpenseReason, service: ExpenseService = Depends(get_expense_service),
                   audit: AuditContext = Depends(get_audit), user: User = Depends(_approve)):
    row = service.reject(expense_id, user, payload.reason)
    audit.log("REJECT", "expense", row.id, f"Rejected expense {_log_summary(row)}", {"reason": payload.reason})
    return row


@router.post("/expenses/{expense_id}/void", response_model=ExpenseTransactionOut)
def void_expense(expense_id: UUID, payload: ExpenseReason, service: ExpenseService = Depends(get_expense_service),
                 audit: AuditContext = Depends(get_audit), user: User = Depends(_approve)):
    row = service.void(expense_id, user, payload.reason)
    audit.log("VOID", "expense", row.id, f"Voided expense {_log_summary(row)}",
              {"amount": row.amount, "reason": payload.reason})
    return row


# ---- budgets ----------------------------------------------------------------------------
@router.get("/budgets", response_model=BudgetStatus, dependencies=[Depends(_read)])
def budget_status(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
                  service: ExpenseService = Depends(get_expense_service)):
    """Budget, approved spending and pending spending per category for one month."""
    return service.budget_status(month)


@router.put("/budgets/{month}", response_model=BudgetStatus)
def set_budgets(payload: BudgetSet, month: str, service: ExpenseService = Depends(get_expense_service),
                audit: AuditContext = Depends(get_audit), user: User = Depends(_approve)):
    if len({l.category for l in payload.lines}) != len(payload.lines):
        raise HTTPException(status_code=422, detail="Each category can appear only once")
    changed = service.set_budgets(month, payload.lines, user)
    if changed:
        audit.log("UPDATE", "budget", month, f"Updated expense budgets for {month}", changed)
    return service.budget_status(month)


@router.post("/budgets/{month}/copy-from/{source_month}", response_model=BudgetStatus)
def copy_budgets(month: str, source_month: str, service: ExpenseService = Depends(get_expense_service),
                 audit: AuditContext = Depends(get_audit), user: User = Depends(_approve)):
    count = service.copy_budgets(source_month, month, user)
    audit.log("UPDATE", "budget", month, f"Copied {count} budget(s) from {source_month} to {month}")
    return service.budget_status(month)
