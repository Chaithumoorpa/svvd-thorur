from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.pagination import PageParams, page_params, set_total
from app.core.rbac import Permission
from app.utils.dependencies import AuditContext, get_audit, get_db, require_permission
from app.services.finance_service import FinanceService
from app.services.finance_report_service import FinanceReportService
from app.services.ledger_service import LedgerService
from app.schemas.finance import (
    IncomeTransactionCreate, IncomeTransactionOut,
    ExpenseTransactionCreate, ExpenseTransactionOut,
    FinanceSummary, LedgerEntry
)
from app.models.user import User

router = APIRouter()

_read = require_permission(Permission.FINANCE_READ)
_write = require_permission(Permission.FINANCE_WRITE)

@router.post("/income", response_model=IncomeTransactionOut, status_code=201)
def add_income(
    income_in: IncomeTransactionCreate,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit),
    current_user: User = Depends(_write),
):
    row = FinanceService.add_income(db, income_in, current_user.id)
    audit.log("CREATE", "income", row.id, f"Recorded income Rs. {row.amount} ({row.source_type.value})",
              {"amount": row.amount, "source": row.source_type, "mode": row.payment_mode})
    return row

@router.post("/expense", response_model=ExpenseTransactionOut, status_code=201)
def add_expense(
    expense_in: ExpenseTransactionCreate,
    db: Session = Depends(get_db),
    audit: AuditContext = Depends(get_audit),
    current_user: User = Depends(_write),
):
    row = FinanceService.add_expense(db, expense_in, current_user.id)
    audit.log("CREATE", "expense", row.id, f"Recorded expense Rs. {row.amount} ({row.category.value})",
              {"amount": row.amount, "category": row.category, "paid_to": row.paid_to})
    return row

@router.get("/summary", response_model=FinanceSummary, dependencies=[Depends(_read)])
def get_summary(db: Session = Depends(get_db)):
    return FinanceService.get_summary(db)

@router.get("/ledger", response_model=List[LedgerEntry], dependencies=[Depends(_read)])
def get_ledger(
    response: Response,
    start_date: Optional[date] = Query(None, description="Start Date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End Date (inclusive)"),
    params: PageParams = Depends(page_params),
    db: Session = Depends(get_db),
):
    """Paginated transaction list (newest first). Total count in `X-Total-Count`."""
    entries, total = FinanceService.get_ledger_page(db, start_date, end_date, params)
    set_total(response, total)
    return entries

@router.get("/ledger/csv", dependencies=[Depends(_read)])
def get_ledger_csv(
    start_date: date = Query(..., description="Start Date"),
    end_date: date = Query(..., description="End Date"),
    db: Session = Depends(get_db)
):
    """
    Download ledger as CSV.
    """
    ledger = LedgerService.generate_ledger(db, start_date, end_date)
    csv_content = LedgerService.generate_ledger_csv(ledger)
    
    response = Response(content=csv_content)
    response.headers["Content-Disposition"] = f"attachment; filename=ledger_{start_date}_{end_date}.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@router.get("/ledger/pdf", dependencies=[Depends(_read)])
def get_ledger_pdf(
    start_date: date = Query(..., description="Start Date"),
    end_date: date = Query(..., description="End Date"),
    db: Session = Depends(get_db)
):
    """
    Download ledger as PDF.
    """
    ledger = LedgerService.generate_ledger(db, start_date, end_date)
    pdf_content = LedgerService.generate_ledger_pdf(ledger, start_date, end_date)
    
    filename = f"Ledger_{start_date}_{end_date}.pdf"
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/reports/monthly", dependencies=[Depends(_read)])
def get_monthly_report(
    year: int = Query(..., description="Year (e.g., 2025)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db)
):
    """
    Get financial summary for a specific month.
    Accessible by ADMIN, TRUSTEE, SUPER_ADMIN.
    """
    return FinanceReportService.generate_monthly_json(db, year, month)

@router.get("/reports/monthly/pdf", dependencies=[Depends(_read)])
def get_monthly_report_pdf(
    year: int = Query(..., description="Year (e.g., 2025)"),
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    db: Session = Depends(get_db)
):
    """
    Download PDF financial report for a specific month.
    Accessible by ADMIN, TRUSTEE, SUPER_ADMIN.
    """
    pdf_content = FinanceReportService.generate_monthly_pdf(db, year, month)
    
    filename = f"Temple_Finance_Report_{year}_{month:02d}.pdf"
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
