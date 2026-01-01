from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.utils.dependencies import get_db, require_admin, get_festival_service
from app.repositories.festival_repo import FestivalRepository
from app.services.festival_service import FestivalService
from app.schemas.festival import FestivalOut, FestivalCreate
from app.models.user import User

router = APIRouter(prefix="/festivals", tags=["Festivals"])




@router.get("/", response_model=List[FestivalOut])
def list_festivals(
    service: FestivalService = Depends(get_festival_service),
):
    return service.list_active_festivals()


@router.get("/{festival_id}", response_model=FestivalOut)
def get_festival(
    festival_id: int,
    service: FestivalService = Depends(get_festival_service),
):
    festival = service.get_festival_details(festival_id)
    if not festival:
        raise HTTPException(status_code=404, detail="Festival not found")
    return festival


@router.post("/", response_model=FestivalOut)
def create_festival(
    payload: FestivalCreate,
    service: FestivalService = Depends(get_festival_service),
    current_user: User = Depends(require_admin),
):
    """Create a new festival. Requires ADMIN or SUPER_ADMIN role."""
    return service.create_festival(payload)
