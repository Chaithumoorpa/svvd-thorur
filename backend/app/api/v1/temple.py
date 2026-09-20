from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.rbac import Permission
from app.models.user import User
from app.repositories.temple_repo import TempleRepository
from app.schemas.temple import TempleOut, TempleUpdate, TimingCreate, TimingOut, TimingUpdate
from app.services.temple_service import TempleService
from app.utils.dependencies import AuditContext, get_audit, get_db, require_permission

router = APIRouter(prefix="/temple", tags=["Temple"])


def get_temple_service(db: Session = Depends(get_db)) -> TempleService:
    return TempleService(TempleRepository(db))


def _cache(response: Response, seconds: int = 60) -> None:
    response.headers["Cache-Control"] = f"public, max-age={seconds}"


# ---- public ---------------------------------------------------------------------------
@router.get("/", response_model=TempleOut)
def get_temple(response: Response, service: TempleService = Depends(get_temple_service)):
    """Public temple profile."""
    _cache(response)
    return service.get_profile()


@router.get("/timings", response_model=List[TimingOut])
def list_timings(response: Response, service: TempleService = Depends(get_temple_service)):
    """Public darshan schedule (active rows only)."""
    _cache(response)
    return service.list_timings(active_only=True)


# ---- admin ----------------------------------------------------------------------------
@router.put("/", response_model=TempleOut)
def update_temple(
    payload: TempleUpdate,
    service: TempleService = Depends(get_temple_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(require_permission(Permission.TEMPLE_WRITE)),
):
    temple = service.update_profile(payload)
    audit.log("UPDATE", "temple", temple.id, "Updated temple profile",
              payload.model_dump(exclude_unset=True, exclude={"history"}))
    return temple


@router.get("/timings/all", response_model=List[TimingOut])
def list_all_timings(
    service: TempleService = Depends(get_temple_service),
    _: User = Depends(require_permission(Permission.TEMPLE_WRITE)),
):
    return service.list_timings(active_only=False)


@router.post("/timings", response_model=TimingOut, status_code=201)
def create_timing(
    payload: TimingCreate,
    service: TempleService = Depends(get_temple_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(require_permission(Permission.TEMPLE_WRITE)),
):
    timing = service.create_timing(payload)
    audit.log("CREATE", "temple_timing", timing.id, f"Added timing '{timing.label}'")
    return timing


@router.put("/timings/{timing_id}", response_model=TimingOut)
def update_timing(
    timing_id: int,
    payload: TimingUpdate,
    service: TempleService = Depends(get_temple_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(require_permission(Permission.TEMPLE_WRITE)),
):
    timing = service.update_timing(timing_id, payload)
    audit.log("UPDATE", "temple_timing", timing.id, f"Updated timing '{timing.label}'",
              payload.model_dump(exclude_unset=True))
    return timing


@router.delete("/timings/{timing_id}", response_model=TimingOut)
def delete_timing(
    timing_id: int,
    service: TempleService = Depends(get_temple_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(require_permission(Permission.TEMPLE_WRITE)),
):
    timing = service.delete_timing(timing_id)
    audit.log("DELETE", "temple_timing", timing_id, f"Deleted timing '{timing.label}'")
    return timing
