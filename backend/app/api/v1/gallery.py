from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.utils.dependencies import get_db, require_admin
from app.repositories.gallery_repo import GalleryRepository
from app.services.gallery_service import GalleryService
from app.schemas.gallery import GalleryOut, GalleryCreate, GalleryUpdate
from app.models.user import User

router = APIRouter(prefix="/gallery", tags=["Gallery"])

def get_gallery_service(db: Session = Depends(get_db)) -> GalleryService:
    repo = GalleryRepository(db)
    return GalleryService(repo)

@router.get("/", response_model=List[GalleryOut])
def list_gallery(
    service: GalleryService = Depends(get_gallery_service),
):
    return service.list_gallery(active_only=True)

@router.post("/", response_model=GalleryOut)
def create_gallery_item(
    payload: GalleryCreate,
    service: GalleryService = Depends(get_gallery_service),
    admin_user: User = Depends(require_admin),
):
    """Create a new gallery item. Requires ADMIN or SUPER_ADMIN role."""
    return service.create_gallery(payload, user_id=admin_user.id)

@router.put("/{gallery_id}", response_model=GalleryOut)
def update_gallery_item(
    gallery_id: int,
    payload: GalleryUpdate,
    service: GalleryService = Depends(get_gallery_service),
    admin_user: User = Depends(require_admin),
):
    """Update a gallery item. Requires ADMIN or SUPER_ADMIN role."""
    return service.update_gallery(gallery_id, payload)

@router.delete("/{gallery_id}", response_model=GalleryOut)
def delete_gallery_item(
    gallery_id: int,
    service: GalleryService = Depends(get_gallery_service),
    admin_user: User = Depends(require_admin),
):
    """Delete a gallery item. Requires ADMIN or SUPER_ADMIN role."""
    return service.delete_gallery(gallery_id)
