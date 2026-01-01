from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.utils.dependencies import get_db, require_admin, require_trustee, get_member_service
from app.services.member_service import MemberService
from app.schemas.member import (
    MemberOut,
    MemberCreate,
    MemberUpdate,
)
from app.models.user import User

router = APIRouter(prefix="/temple-members", tags=["Temple Members"])


@router.get("/", response_model=List[MemberOut])
def list_members(
    service: MemberService = Depends(get_member_service),
    current_user: User = Depends(require_admin),
):
    """List all members. Requires ADMIN or SUPER_ADMIN role."""
    return service.list_members()


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
    current_user: User = Depends(require_admin),
):
    """Get member by ID. Requires ADMIN or SUPER_ADMIN role."""
    return service.get_member(member_id)


@router.post("/", response_model=MemberOut)
def create_member(
    payload: MemberCreate,
    service: MemberService = Depends(get_member_service),
    current_user: User = Depends(require_admin),
):
    """Create a new member profile. Requires ADMIN or SUPER_ADMIN role."""
    return service.create_member(payload)


@router.put("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    payload: MemberUpdate,
    service: MemberService = Depends(get_member_service),
    current_user: User = Depends(require_admin),
):
    """Update a member profile. Requires ADMIN or SUPER_ADMIN role."""
    return service.update_member(member_id, payload)


@router.delete("/{member_id}", response_model=MemberOut)
def delete_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
    current_user: User = Depends(require_admin),
):
    """Delete a member profile. Requires ADMIN or SUPER_ADMIN role."""
    return service.delete_member(member_id)
