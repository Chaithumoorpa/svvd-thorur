from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict

from app.core.pagination import PageParams, page_params, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.services.audit_service import AuditService
from app.utils.dependencies import get_audit_service, require_permission

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


class AuditLogOut(BaseModel):
    id: int
    actor_username: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    summary: Optional[str] = None
    changes: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    response: Response,
    entity_type: Optional[str] = Query(None, max_length=50),
    action: Optional[str] = Query(None, max_length=30),
    actor: Optional[str] = Query(None, max_length=100),
    service: AuditService = Depends(get_audit_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Who changed what and when (SUPER_ADMIN). Newest first."""
    items, total = service.list_page(params, entity_type, action, actor)
    set_total(response, total)
    return items
