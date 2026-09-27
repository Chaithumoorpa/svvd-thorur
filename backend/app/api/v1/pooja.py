from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.cache import cached, invalidate
from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.blessing import SevaCalendarDay, SevaDay
from app.schemas.pooja import PoojaCreate, PoojaOut, PoojaUpdate
from app.services.blessing_service import MAX_CALENDAR_DAYS, BlessingService
from app.services.pooja_service import PoojaService
from app.utils.dependencies import (
    AuditContext, get_audit, get_blessing_service, get_pooja_service, require_permission,
)

router = APIRouter(prefix="/poojas", tags=["Poojas"])

_can_write = require_permission(Permission.CONTENT_WRITE)


@router.get("", response_model=List[PoojaOut])
def list_poojas(response: Response, service: PoojaService = Depends(get_pooja_service)):
    """Public list of active poojas / sevas - admin-curated and small, but
    capped rather than truly unbounded, and server-side cached."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return cached("poojas:list", lambda: [PoojaOut.model_validate(p) for p in service.list_active_poojas()])


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


@router.get("/{pooja_id}/calendar", response_model=List[SevaCalendarDay])
def get_seva_calendar(
    response: Response,
    pooja_id: int,
    start: date,
    end: date,
    service: BlessingService = Depends(get_blessing_service),
):
    """Public: the seva's bookings per day from `start` to `end` (inclusive) -
    the rolling contribution-style grid behind the Abhishekam calendar."""
    if end < start or (end - start).days >= MAX_CALENDAR_DAYS:
        raise HTTPException(status_code=400, detail=f"Choose a range of 1 to {MAX_CALENDAR_DAYS} days.")
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.calendar(pooja_id, start, end)


@router.get("/{pooja_id}/calendar/{day}", response_model=SevaDay)
def get_seva_day(
    response: Response,
    pooja_id: int,
    day: date,
    service: BlessingService = Depends(get_blessing_service),
):
    """Public: one day - a calendar square's pop-up, and that date's public
    blessings page. Only bookings the devotee chose to show, once paid for."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return service.day(pooja_id, day)


@router.post("", response_model=PoojaOut, status_code=201)
def create_pooja(
    payload: PoojaCreate,
    service: PoojaService = Depends(get_pooja_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    pooja = service.create_pooja(payload)
    audit.log("CREATE", "pooja", pooja.id, f"Created pooja '{pooja.name}'")
    invalidate("poojas:")
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
    invalidate("poojas:")
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
    invalidate("poojas:")
    return pooja
