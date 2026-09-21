from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate
from app.services.announcement_service import AnnouncementService
from app.utils.dependencies import AuditContext, get_announcement_service, get_audit, require_permission

router = APIRouter(prefix="/announcements", tags=["Announcements"])

_can_write = require_permission(Permission.CONTENT_WRITE)


# ---- public: only published announcements (active and inside their date window) ----------
@router.get("", response_model=List[AnnouncementOut])
def list_announcements(
    limit: Optional[int] = Query(None, ge=1, le=50),
    service: AnnouncementService = Depends(get_announcement_service),
):
    return service.list_published(limit=limit)


# ---- admin: everything incl. inactive/expired (declared before /{id}) ---------------------
@router.get("/admin/all", response_model=List[AnnouncementOut])
def list_all_announcements(
    response: Response,
    service: AnnouncementService = Depends(get_announcement_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_can_write),
):
    items, total = paginate(service.query_all(), params)
    set_total(response, total)
    return items


@router.get("/{announcement_id}", response_model=AnnouncementOut)
def get_announcement(
    announcement_id: int,
    service: AnnouncementService = Depends(get_announcement_service),
):
    return service.get_published(announcement_id)


@router.post("", response_model=AnnouncementOut, status_code=201)
def create_announcement(
    payload: AnnouncementCreate,
    service: AnnouncementService = Depends(get_announcement_service),
    audit: AuditContext = Depends(get_audit),
    current_user: User = Depends(_can_write),
):
    result = service.create_announcement(payload, current_user.id)
    audit.log("CREATE", "announcement", result.id, f"Created announcement '{result.title}'")
    return result


@router.put("/{announcement_id}", response_model=AnnouncementOut)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    service: AnnouncementService = Depends(get_announcement_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    changes = payload.model_dump(exclude_unset=True)
    result = service.update_announcement(announcement_id, changes)
    audit.log("UPDATE", "announcement", announcement_id, f"Updated announcement '{result.title}'", changes)
    return result


@router.delete("/{announcement_id}", response_model=AnnouncementOut)
def delete_announcement(
    announcement_id: int,
    service: AnnouncementService = Depends(get_announcement_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    """Soft delete (unpublishes). The row is kept for history."""
    result = service.delete_announcement(announcement_id)
    audit.log("DELETE", "announcement", announcement_id, f"Unpublished announcement '{result.title}'")
    return result
