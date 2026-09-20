from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.utils.dependencies import get_db, require_admin, require_trustee, require_super_admin
from app.services.finance_service import FinanceService
from app.services.finance_report_service import FinanceReportService
from app.services.ledger_service import LedgerService
from app.schemas.finance import (
    IncomeTransactionCreate, IncomeTransactionOut,
    ExpenseTransactionCreate, ExpenseTransactionOut,
    FinanceSummary, LedgerEntry
)
from app.models.user import User
import csv
import io

router = APIRouter()

@router.post("/income", response_model=IncomeTransactionOut, dependencies=[Depends(require_admin)])
def add_income(
    income_in: IncomeTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return FinanceService.add_income(db, income_in, current_user.id)

@router.post("/expense", response_model=ExpenseTransactionOut, dependencies=[Depends(require_admin)])
def add_expense(
    expense_in: ExpenseTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return FinanceService.add_expense(db, expense_in, current_user.id)

@router.get("/summary", response_model=FinanceSummary, dependencies=[Depends(require_trustee)])
def get_summary(db: Session = Depends(get_db)):
    return FinanceService.get_summary(db)

@router.get("/ledger", response_model=List[LedgerEntry], dependencies=[Depends(require_trustee)])
def get_ledger(
    start_date: Optional[date] = Query(None, description="Start Date"),
    end_date: Optional[date] = Query(None, description="End Date"),
    db: Session = Depends(get_db)
):
    """
    Get simple transaction list for dashboard views.
    """
    return FinanceService.get_ledger(db, start_date, end_date)

@router.get("/ledger/csv", dependencies=[Depends(require_trustee)])
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

@router.get("/ledger/pdf", dependencies=[Depends(require_trustee)])
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

@router.get("/reports/monthly", dependencies=[Depends(require_trustee)])
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

@router.get("/reports/monthly/pdf", dependencies=[Depends(require_trustee)])
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
