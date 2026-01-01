from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from app.utils.dependencies import (
    get_pooja_repository,
    get_announcement_repository,
    get_donor_repository,
    get_gallery_repository,
    get_member_repository,
    get_seva_ticket_repository
)
from app.repositories.pooja_repo import PoojaRepository
from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.donor_repo import DonorRepository
from app.repositories.gallery_repo import GalleryRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.seva_ticket_repo import SevaTicketRepository

class MetaResponse(BaseModel):
    service: str
    version: str
    status: str

class DashboardStats(BaseModel):
    poojas: int
    announcements: int
    donors: int
    gallery: int
    members: int
    seva_tickets: int
    seva_tickets_today: int

class ActivityItem(BaseModel):
    text: str
    time: str
    icon: str
    color: str

router = APIRouter(prefix="/meta", tags=["Meta"])

@router.get("/", response_model=MetaResponse)
def get_meta():
    """Get service metadata and health status."""
    return MetaResponse(
        service="SVVD Temple Backend",
        version="1.0.0",
        status="active"
    )

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    pooja_repo: PoojaRepository = Depends(get_pooja_repository),
    announcement_repo: AnnouncementRepository = Depends(get_announcement_repository),
    donor_repo: DonorRepository = Depends(get_donor_repository),
    gallery_repo: GalleryRepository = Depends(get_gallery_repository),
    member_repo: MemberRepository = Depends(get_member_repository),
    ticket_repo: SevaTicketRepository = Depends(get_seva_ticket_repository)
):
    """Fetch real-time counts for the admin dashboard."""
    return DashboardStats(
        poojas=pooja_repo.count(),
        announcements=announcement_repo.count(),
        donors=donor_repo.count(),
        gallery=gallery_repo.count(),
        members=member_repo.count(),
        seva_tickets=ticket_repo.count(),
        seva_tickets_today=ticket_repo.count_today()
    )

@router.get("/activity", response_model=List[ActivityItem])
def get_recent_activity():
    """Fetch recent system activity (Mocked for now, can be connected to an AuditLog table later)."""
    # In a real system, you'd fetch this from a 'logs' or 'activity' table
    return [
        { "text": "New member registered", "time": "2 hours ago", "icon": "Users", "color": "text-blue-500" },
        { "text": "Seva ticket scanned", "time": "5 hours ago", "icon": "Ticket", "color": "text-orange-500" },
        { "text": "Donation recorded", "time": "1 day ago", "icon": "Heart", "color": "text-red-500" },
        { "text": "Pooja updated", "time": "2 days ago", "icon": "Calendar", "color": "text-emerald-500" },
    ]
