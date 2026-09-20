from typing import List

from fastapi import APIRouter, Depends, Response

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.pooja import PoojaCreate, PoojaOut, PoojaUpdate
from app.services.pooja_service import PoojaService
from app.utils.dependencies import AuditContext, get_audit, get_pooja_service, require_permission

router = APIRouter(prefix="/poojas", tags=["Poojas"])

_can_write = require_permission(Permission.CONTENT_WRITE)


@router.get("/", response_model=List[PoojaOut])
def list_poojas(service: PoojaService = Depends(get_pooja_service)):
    """Public list of active poojas / sevas."""
    return service.list_active_poojas()


@router.get("/admin/all", response_model=List[PoojaOut])
def list_all_poojas(
    response: Response,
    service: PoojaService = Depends(get_pooja_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_can_write),
):
    items, total = paginate(service.query_all(), params)
    set_total(response, total)
    return items


@router.get("/{pooja_id}", response_model=PoojaOut)
def get_pooja(pooja_id: int, service: PoojaService = Depends(get_pooja_service)):
    return service.get_pooja(pooja_id)


@router.post("/", response_model=PoojaOut, status_code=201)
def create_pooja(
    payload: PoojaCreate,
    service: PoojaService = Depends(get_pooja_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    pooja = service.create_pooja(payload)
    audit.log("CREATE", "pooja", pooja.id, f"Created pooja '{pooja.name}'")
    return pooja


@router.put("/{pooja_id}", response_model=PoojaOut)
def update_pooja(
    pooja_id: int,
    payload: PoojaUpdate,
    service: PoojaService = Depends(get_pooja_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    pooja = service.update_pooja(pooja_id, payload)
    audit.log("UPDATE", "pooja", pooja_id, f"Updated pooja '{pooja.name}'",
              payload.model_dump(exclude_unset=True))
    return pooja


@router.delete("/{pooja_id}", response_model=PoojaOut)
def delete_pooja(
    pooja_id: int,
    service: PoojaService = Depends(get_pooja_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    """Soft delete (hides the pooja). Existing seva tickets keep referencing it."""
    pooja = service.delete_pooja(pooja_id)
    audit.log("DELETE", "pooja", pooja_id, f"Removed pooja '{pooja.name}'")
    return pooja
