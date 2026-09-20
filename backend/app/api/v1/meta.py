from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.rbac import Permission, has_permission
from app.models.contact import ContactMessage, ContactStatus
from app.models.festival import Festival
from app.models.user import User
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.donor_repo import DonorRepository
from app.repositories.gallery_repo import GalleryRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.pooja_repo import PoojaRepository
from app.repositories.seva_ticket_repo import SevaTicketRepository
from app.services.audit_service import AuditService
from app.utils.dependencies import get_audit_service, get_db, require_permission


class MetaResponse(BaseModel):
    service: str
    version: str
    status: str


class DashboardStats(BaseModel):
    """Counts the caller is allowed to see; everything else is reported as 0."""
    poojas: int
    announcements: int
    donors: int
    gallery: int
    members: int
    seva_tickets: int
    seva_tickets_today: int
    pending_messages: int = 0
    upcoming_festivals: int = 0


class ActivityItem(BaseModel):
    id: int
    text: str
    actor: str | None = None
    action: str
    entity_type: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/", response_model=MetaResponse)
def get_meta():
    """Service metadata (public, non-sensitive)."""
    return MetaResponse(service="SVVD Temple Backend", version="2.0.0", status="active")


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.DASHBOARD_VIEW)),
):
    """Admin dashboard counts. Requires dashboard access; private counts obey per-module permissions."""
    can = lambda p: has_permission(user.roles, p)  # noqa: E731
    tickets = SevaTicketRepository(db)
    today = date.today()
    return DashboardStats(
        poojas=PoojaRepository(db).count(),
        announcements=AnnouncementRepository(db).count(),
        gallery=GalleryRepository(db).count(),
        donors=DonorRepository(db).count() if can(Permission.DONORS_READ) else 0,
        members=MemberRepository(db).count() if can(Permission.MEMBERS_READ) else 0,
        seva_tickets=tickets.count() if can(Permission.TICKETS_MANAGE) else 0,
        seva_tickets_today=tickets.count_today() if can(Permission.TICKETS_MANAGE) else 0,
        pending_messages=(
            db.query(ContactMessage).filter(ContactMessage.status == ContactStatus.PENDING).count()
            if can(Permission.MESSAGES_MANAGE) else 0
        ),
        upcoming_festivals=db.query(Festival).filter(
            Festival.is_active.is_(True), Festival.festival_date >= today
        ).count(),
    )


@router.get("/activity", response_model=List[ActivityItem])
def get_recent_activity(
    audit: AuditService = Depends(get_audit_service),
    _: User = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Recent changes from the audit log (SUPER_ADMIN)."""
    return [
        ActivityItem(id=e.id, text=e.summary or f"{e.action} {e.entity_type}", actor=e.actor_username,
                     action=e.action, entity_type=e.entity_type, created_at=e.created_at)
        for e in audit.recent(8)
    ]
