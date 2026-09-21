from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.gallery import GalleryCreate, GalleryOut, GalleryUpdate
from app.schemas.upload import UploadUrlRequest, UploadUrlResponse
from app.services.gallery_service import GalleryService
from app.services.storage_service import StorageService
from app.utils.dependencies import (
    AuditContext,
    get_audit,
    get_gallery_service,
    get_storage_service,
    require_permission,
)

router = APIRouter(prefix="/gallery", tags=["Gallery"])

_can_write = require_permission(Permission.CONTENT_WRITE)


@router.post("/upload-url", response_model=UploadUrlResponse)
def create_upload_url(
    payload: UploadUrlRequest,
    storage: StorageService = Depends(get_storage_service),
    _: User = Depends(_can_write),
):
    """Presigned S3 upload for a gallery photo. The browser uploads the file
    directly to S3 with the returned fields, then saves `public_url` as the
    gallery item's image_url. 503 if S3 isn't configured (no S3_BUCKET_NAME)."""
    return storage.create_upload(payload.content_type)


@router.get("/", response_model=List[GalleryOut])
def list_gallery(
    response: Response,
    category: Optional[str] = Query(None, max_length=50),
    service: GalleryService = Depends(get_gallery_service),
    params: PageParams = Depends(page_params),
):
    """Public gallery (active items only). Paginated; total in `X-Total-Count`."""
    items, total = paginate(service.query(active_only=True, category=category), params)
    set_total(response, total)
    response.headers["Cache-Control"] = "public, max-age=60"
    return items


@router.get("/admin/all", response_model=List[GalleryOut])
def list_all_gallery(
    response: Response,
    service: GalleryService = Depends(get_gallery_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_can_write),
):
    items, total = paginate(service.query(active_only=False), params)
    set_total(response, total)
    return items


@router.post("/", response_model=GalleryOut, status_code=201)
def create_gallery_item(
    payload: GalleryCreate,
    service: GalleryService = Depends(get_gallery_service),
    audit: AuditContext = Depends(get_audit),
    user: User = Depends(_can_write),
):
    item = service.create_gallery(payload, user_id=user.id)
    audit.log("CREATE", "gallery", item.id, f"Added gallery item '{item.title}'")
    return item


@router.put("/{gallery_id}", response_model=GalleryOut)
def update_gallery_item(
    gallery_id: int,
    payload: GalleryUpdate,
    service: GalleryService = Depends(get_gallery_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    item = service.update_gallery(gallery_id, payload)
    audit.log("UPDATE", "gallery", gallery_id, f"Updated gallery item '{item.title}'",
              payload.model_dump(exclude_unset=True))
    return item


@router.delete("/{gallery_id}", response_model=GalleryOut)
def delete_gallery_item(
    gallery_id: int,
    service: GalleryService = Depends(get_gallery_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    item = service.delete_gallery(gallery_id)
    audit.log("DELETE", "gallery", gallery_id, f"Deleted gallery item '{item.title}'")
    return item
