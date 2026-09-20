from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import cast, func, select, DateTime
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.models.donor import Donor
from app.models.member import Member
from app.models.pooja import Pooja
from app.models.seva_ticket import SevaTicket
from app.models.user import User
from app.utils.dependencies import (
    get_db,
    require_admin,
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
    admin_user: User = Depends(require_admin),
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

def _time_ago(then: datetime, now: datetime) -> str:
    seconds = max(int((now - then).total_seconds()), 0)
    if seconds < 60:
        return "just now"
    for size, unit in ((86400, "day"), (3600, "hour"), (60, "minute")):
        if seconds >= size:
            n = seconds // size
            return f"{n} {unit}{'s' if n != 1 else ''} ago"
    return "just now"


@router.get("/activity", response_model=List[ActivityItem])
def get_recent_activity(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Recent activity for the admin dashboard, built from real records.
    (This endpoint used to return four hard-coded fake events to every visitor.)
    No donor or devotee names are included.
    """
    # Compare against the database clock cast to a naive timestamp, the same way
    # created_at/updated_at (server-side now()) are stored.
    now = db.scalar(select(cast(func.now(), DateTime)))

    sources = [
        (Member, "created_at", "Users", "text-blue-500", lambda r: "New temple member added"),
        (SevaTicket, "created_at", "Ticket", "text-orange-500", lambda r: f"Seva ticket {r.ticket_number} issued"),
        (Donor, "created_at", "Heart", "text-red-500", lambda r: f"Donation of Rs. {r.amount} recorded"),
        (Pooja, "updated_at", "Calendar", "text-emerald-500", lambda r: f"Pooja '{r.name}' updated"),
    ]

    events = []
    for model, ts_attr, icon, color, describe in sources:
        ts_col = getattr(model, ts_attr)
        for row in db.query(model).order_by(ts_col.desc()).limit(5).all():
            events.append((getattr(row, ts_attr), describe(row), icon, color))

    events.sort(key=lambda e: e[0], reverse=True)
    return [
        {"text": text, "time": _time_ago(ts, now), "icon": icon, "color": color}
        for ts, text, icon, color in events[:8]
    ]
