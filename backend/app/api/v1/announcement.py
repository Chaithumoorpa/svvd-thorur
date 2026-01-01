from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.utils.dependencies import get_db, require_admin, get_announcement_service
from app.repositories.announcement_repo import AnnouncementRepository
from app.services.announcement_service import AnnouncementService
from app.schemas.announcement import AnnouncementOut, AnnouncementCreate, AnnouncementUpdate
from app.models.user import User

router = APIRouter(prefix="/announcements", tags=["Announcements"])
logger = logging.getLogger(__name__)




@router.get("/", response_model=List[AnnouncementOut])
def list_announcements(
    show_all: bool = False,
    service: AnnouncementService = Depends(get_announcement_service),
):
    if show_all:
        return service.list_all_announcements()
    return service.list_active_announcements()


@router.get("/{announcement_id}", response_model=AnnouncementOut)
def get_announcement(
    announcement_id: int,
    service: AnnouncementService = Depends(get_announcement_service),
):
    announcement = service.get_announcement_details(announcement_id)
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return announcement


@router.post("/", response_model=AnnouncementOut)
def create_announcement(
    payload: AnnouncementCreate,
    service: AnnouncementService = Depends(get_announcement_service),
    current_user: User = Depends(require_admin),
):
    """Create a new announcement. Requires ADMIN or SUPER_ADMIN role."""
    logger.info(
        f"Announcement POST: user={current_user.username}, "
        f"roles={current_user.roles}, title={payload.title}"
    )
    try:
        result = service.create_announcement(payload)
        logger.info(f"Announcement created: id={result.id}, title={result.title}")
        return result
    except Exception as e:
        logger.exception(f"Announcement creation failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Announcement creation failed. Please check server logs."
        )


@router.put("/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    service: AnnouncementService = Depends(get_announcement_service),
    current_user: User = Depends(require_admin),
):
    """Update an announcement. Requires ADMIN or SUPER_ADMIN role."""
    logger.info(
        f"Announcement PUT: user={current_user.username}, "
        f"roles={current_user.roles}, announcement_id={announcement_id}"
    )
    result = service.update_announcement(announcement_id, payload.dict(exclude_unset=True))
    logger.info(f"Announcement updated: id={announcement_id}")
    return result


@router.delete("/{announcement_id}", response_model=AnnouncementOut)
def delete_announcement(
    announcement_id: int,
    service: AnnouncementService = Depends(get_announcement_service),
    current_user: User = Depends(require_admin),
):
    """Delete an announcement. Requires ADMIN or SUPER_ADMIN role."""
    logger.info(
        f"Announcement DELETE: user={current_user.username}, "
        f"roles={current_user.roles}, announcement_id={announcement_id}"
    )
    result = service.delete_announcement(announcement_id)
    logger.info(f"Announcement deleted: id={announcement_id}")
    return result
