from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.pagination import PageParams, page_params, paginate, set_total
from app.core.rbac import Permission
from app.models.contact import ContactStatus
from app.models.user import User
from app.schemas.contact import ContactCreate, ContactOut, ContactPublicAck, ContactUpdate
from app.services.contact_service import ContactService
from app.utils.dependencies import AuditContext, get_audit, get_contact_service, require_permission
from app.utils.rate_limiter import contact_limiter, get_client_ip

router = APIRouter(prefix="/contacts", tags=["Contact Us"])

_can_manage = require_permission(Permission.MESSAGES_MANAGE)


@router.post("", response_model=ContactPublicAck, status_code=201)
def submit_contact_message(
    payload: ContactCreate,
    request: Request,
    service: ContactService = Depends(get_contact_service),
):
    """Public contact form. Rate limited per IP; honeypot field silently drops bot posts."""
    if not contact_limiter.is_allowed(get_client_ip(request)):
        raise HTTPException(status_code=429, detail="Too many messages. Please try again later.")
    if payload.website:  # honeypot tripped: pretend success without storing anything
        return ContactPublicAck(id=0, status=ContactStatus.PENDING)
    return service.submit_message(payload)


@router.get("", response_model=List[ContactOut])
def list_contact_messages(
    response: Response,
    status: Optional[ContactStatus] = None,
    service: ContactService = Depends(get_contact_service),
    params: PageParams = Depends(page_params),
    _: User = Depends(_can_manage),
):
    items, total = paginate(service.query_messages(status), params)
    set_total(response, total)
    return items


@router.get("/{message_id}", response_model=ContactOut)
def get_contact_message(
    message_id: int,
    service: ContactService = Depends(get_contact_service),
    _: User = Depends(_can_manage),
):
    return service.get_message_details(message_id)


@router.patch("/{message_id}", response_model=ContactOut)
def update_contact_message(
    message_id: int,
    payload: ContactUpdate,
    service: ContactService = Depends(get_contact_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_manage),
):
    message = service.update_message(message_id, payload)
    audit.log("UPDATE", "contact_message", message_id, f"Updated message #{message_id}",
              {"status": message.status})
    return message


@router.delete("/{message_id}")
def delete_contact_message(
    message_id: int,
    service: ContactService = Depends(get_contact_service),
    audit: AuditContext = Depends(get_audit),
    _: User = Depends(_can_manage),
):
    service.delete_message(message_id)
    audit.log("DELETE", "contact_message", message_id, f"Deleted message #{message_id}")
    return {"message": "Deleted successfully"}
