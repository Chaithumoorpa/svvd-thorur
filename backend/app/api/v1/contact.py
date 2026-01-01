from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.utils.dependencies import get_contact_service, require_admin
from app.services.contact_service import ContactService
from app.schemas.contact import ContactCreate, ContactOut, ContactUpdate
from app.models.contact import ContactStatus
from app.models.user import User

router = APIRouter(prefix="/contacts", tags=["Contact Us"])

@router.post("/", response_model=ContactOut)
def submit_contact_message(
    payload: ContactCreate,
    service: ContactService = Depends(get_contact_service),
):
    """Public endpoint to submit a contact message."""
    return service.submit_message(payload)

@router.get("/", response_model=List[ContactOut])
def list_contact_messages(
    status: Optional[ContactStatus] = None,
    service: ContactService = Depends(get_contact_service),
    admin_user: User = Depends(require_admin),
):
    """Admin endpoint to list all contact messages."""
    return service.list_messages(status)

@router.get("/{message_id}", response_model=ContactOut)
def get_contact_message(
    message_id: int,
    service: ContactService = Depends(get_contact_service),
    admin_user: User = Depends(require_admin),
):
    """Admin endpoint to get details of a specific contact message."""
    return service.get_message_details(message_id)

@router.patch("/{message_id}", response_model=ContactOut)
def update_contact_message(
    message_id: int,
    payload: ContactUpdate,
    service: ContactService = Depends(get_contact_service),
    admin_user: User = Depends(require_admin),
):
    """Admin endpoint to update status or add notes to a contact message."""
    return service.update_message(message_id, payload)

@router.delete("/{message_id}")
def delete_contact_message(
    message_id: int,
    service: ContactService = Depends(get_contact_service),
    admin_user: User = Depends(require_admin),
):
    """Admin endpoint to delete a contact message."""
    service.delete_message(message_id)
    return {"message": "Deleted successfully"}
