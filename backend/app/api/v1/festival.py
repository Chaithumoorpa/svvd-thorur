from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.festival import FestivalCreate, FestivalOut, FestivalUpdate
from app.services.festival_service import FestivalService
from app.utils.dependencies import AuditContext, get_audit, get_festival_service, require_permission

router = APIRouter(prefix="/festivals", tags=["Festivals"])

_can_write = require_permission(Permission.CONTENT_WRITE)


@router.get("/", response_model=List[FestivalOut])
def list_festivals(
    upcoming: bool = Query(False, description="Only festivals that have not ended yet"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    service: FestivalService = Depends(get_festival_service),
):
    return service.list_active_festivals(upcoming_only=upcoming, limit=limit)


@router.get("/admin/all", response_model=List[FestivalOut])
def list_all_festivals(
    response: Response,
    service: FestivalService = Depends(get_festival_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_can_write),
):
    items, total = paginate(service.query_all(), params)
    set_total(response, total)
    return items


@router.get("/{festival_id}", response_model=FestivalOut)
def get_festival(festival_id: int, service: FestivalService = Depends(get_festival_service)):
    return service.get_festival_details(festival_id)


@router.post("/", response_model=FestivalOut, status_code=201)
def create_festival(
    payload: FestivalCreate,
    service: FestivalService = Depends(get_festival_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    festival = service.create_festival(payload)
    audit.log("CREATE", "festival", festival.id, f"Created festival '{festival.name}'")
    return festival


@router.put("/{festival_id}", response_model=FestivalOut)
def update_festival(
    festival_id: int,
    payload: FestivalUpdate,
    service: FestivalService = Depends(get_festival_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    festival = service.update_festival(festival_id, payload)
    audit.log("UPDATE", "festival", festival_id, f"Updated festival '{festival.name}'",
              payload.model_dump(exclude_unset=True))
    return festival


@router.delete("/{festival_id}", response_model=FestivalOut)
def delete_festival(
    festival_id: int,
    service: FestivalService = Depends(get_festival_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    festival = service.delete_festival(festival_id)
    audit.log("DELETE", "festival", festival_id, f"Removed festival '{festival.name}'")
    return festival
