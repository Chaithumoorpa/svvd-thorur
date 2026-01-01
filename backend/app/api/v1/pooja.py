from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.utils.dependencies import get_db, require_admin, get_pooja_service
from app.repositories.pooja_repo import PoojaRepository
from app.services.pooja_service import PoojaService
from app.schemas.pooja import PoojaOut, PoojaCreate, PoojaUpdate
from app.models.user import User

router = APIRouter(prefix="/poojas", tags=["Poojas"])




@router.get("/", response_model=List[PoojaOut])
def list_poojas(
    service: PoojaService = Depends(get_pooja_service),
):
    return service.list_active_poojas()


@router.get("/{pooja_id}", response_model=PoojaOut)
def get_pooja(
    pooja_id: int,
    service: PoojaService = Depends(get_pooja_service),
):
    pooja = service.get_pooja_details(pooja_id)
    if not pooja:
        raise HTTPException(status_code=404, detail="Pooja not found")
    return pooja


@router.post("/", response_model=PoojaOut)
def create_pooja(
    payload: PoojaCreate,
    service: PoojaService = Depends(get_pooja_service),
    admin_user: User = Depends(require_admin),
):
    """Create a new pooja. Requires ADMIN or SUPER_ADMIN role."""
    return service.create_pooja(payload)


@router.put("/{pooja_id}", response_model=PoojaOut)
def update_pooja(
    pooja_id: int,
    payload: PoojaUpdate,
    service: PoojaService = Depends(get_pooja_service),
    admin_user: User = Depends(require_admin),
):
    """Update a pooja. Requires ADMIN or SUPER_ADMIN role."""
    return service.update_pooja(pooja_id, payload)


@router.delete("/{pooja_id}", response_model=PoojaOut)
def delete_pooja(
    pooja_id: int,
    service: PoojaService = Depends(get_pooja_service),
    admin_user: User = Depends(require_admin),
):
    """Delete a pooja. Requires ADMIN or SUPER_ADMIN role."""
    return service.delete_pooja(pooja_id)
