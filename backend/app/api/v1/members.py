from typing import List

from fastapi import APIRouter, Depends, Response

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.user import User
from app.schemas.member import MemberCreate, MemberOut, MemberUpdate
from app.schemas.upload import UploadUrlRequest, UploadUrlResponse
from app.services.member_service import MemberService
from app.services.storage_service import StorageService
from app.utils.dependencies import (
    AuditContext, get_audit, get_member_service, get_storage_service, require_permission,
)

router = APIRouter(prefix="/temple-members", tags=["Temple Members"])

_can_read = require_permission(Permission.MEMBERS_READ)
_can_write = require_permission(Permission.MEMBERS_WRITE)


@router.post("/upload-url", response_model=UploadUrlResponse)
def create_member_photo_upload_url(
    payload: UploadUrlRequest,
    storage: StorageService = Depends(get_storage_service),
    _: User = Depends(_can_write),
):
    """Presigned S3 upload for a member's photo. Uses a nested gallery/members
    prefix so the upload stays under the bucket policy's public-read gallery/*
    prefix without needing its own policy change - member photos are only
    ever shown when show_on_website is set, so public read is fine."""
    return storage.create_upload(payload.content_type, key_prefix="gallery/members")


@router.get("", response_model=List[MemberOut])
def list_members(
    response: Response,
    service: MemberService = Depends(get_member_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_can_read),
):
    """Private member directory (contains phone/email). TRUSTEE and above."""
    items, total = paginate(service.query_members(), params)
    set_total(response, total)
    return items


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
    _: User = Depends(_can_read),
):
    return service.get_member(member_id)


@router.post("", response_model=MemberOut, status_code=201)
def create_member(
    payload: MemberCreate,
    service: MemberService = Depends(get_member_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    member = service.create_member(payload)
    audit.log("CREATE", "member", member.id, f"Added member {member.name}")
    return member


@router.put("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    payload: MemberUpdate,
    service: MemberService = Depends(get_member_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    member = service.update_member(member_id, payload)
    # contact details are personal data: log which fields changed, not their values
    audit.log("UPDATE", "member", member_id, f"Updated member {member.name}",
              {"fields": sorted(payload.model_dump(exclude_unset=True).keys())})
    return member


@router.delete("/{member_id}", response_model=MemberOut)
def delete_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_write),
):
    member = service.delete_member(member_id)
    audit.log("DELETE", "member", member_id, f"Removed member {member.name}")
    return member
