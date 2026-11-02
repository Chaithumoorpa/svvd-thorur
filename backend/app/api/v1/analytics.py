"""Admin analytics: finance, inventory and audit-log trends. Read-only; each
section needs the same permission as the module it summarises."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.rbac import Permission
from app.schemas.analytics import AuditAnalytics, FinanceAnalytics, InventoryAnalytics
from app.services.analytics_service import AnalyticsService
from app.utils.dependencies import get_db, require_permission

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/finance", response_model=FinanceAnalytics,
            dependencies=[Depends(require_permission(Permission.FINANCE_READ))])
def finance(months: int = Query(12, ge=1, le=36), service: AnalyticsService = Depends(get_analytics_service)):
    """Income vs approved expenses per month, breakdowns, top payees, donations -
    with the previous period of the same length for comparison."""
    return service.finance(months)


@router.get("/inventory", response_model=InventoryAnalytics,
            dependencies=[Depends(require_permission(Permission.INVENTORY_READ))])
def inventory(months: int = Query(12, ge=1, le=36), service: AnalyticsService = Depends(get_analytics_service)):
    """Stock value by category, monthly consumption and the items used most."""
    return service.inventory(months)


@router.get("/audit", response_model=AuditAnalytics,
            dependencies=[Depends(require_permission(Permission.AUDIT_READ))])
def audit(days: int = Query(30, ge=1, le=365), service: AnalyticsService = Depends(get_analytics_service)):
    """Who did what and when: activity per day and hour (IST), by person, action and
    area; sign-ins and failed sign-ins; deletions, off-hours and other sensitive events."""
    return service.audit(days)
