"""
Read-only, unauthenticated endpoints for the public website.

Everything returned here goes through explicit *public* schemas so private fields
(member phone/email, donor data, inactive content) can never leak by accident.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.repositories.announcement_repo import AnnouncementRepository
from app.repositories.festival_repo import FestivalRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.pooja_repo import PoojaRepository
from app.repositories.temple_repo import TempleRepository
from app.schemas.announcement import AnnouncementOut
from app.schemas.festival import FestivalOut
from app.schemas.pooja import PoojaOut
from app.schemas.temple import CommitteeMemberPublic, TempleOut, TimingOut
from app.utils.dependencies import get_db

router = APIRouter(prefix="/public", tags=["Public"])

HOME_ANNOUNCEMENTS = 3
HOME_FESTIVALS = 3
HOME_POOJAS = 4


class HomePayload(BaseModel):
    temple: Optional[TempleOut] = None
    timings: List[TimingOut]
    announcements: List[AnnouncementOut]
    festivals: List[FestivalOut]
    poojas: List[PoojaOut]


@router.get("/home", response_model=HomePayload)
def home(response: Response, db: Session = Depends(get_db)):
    """Everything the landing page needs in ONE request."""
    from datetime import date

    response.headers["Cache-Control"] = "public, max-age=30"
    temples = TempleRepository(db)
    return HomePayload(
        temple=TempleOut.model_validate(t) if (t := temples.get_active()) else None,
        timings=[TimingOut.model_validate(x) for x in temples.list_timings(active_only=True)],
        announcements=[AnnouncementOut.model_validate(a)
                       for a in AnnouncementRepository(db).get_all_active(limit=HOME_ANNOUNCEMENTS)],
        festivals=[FestivalOut.model_validate(f)
                   for f in FestivalRepository(db).get_all(upcoming_from=date.today(), limit=HOME_FESTIVALS)],
        poojas=[PoojaOut.model_validate(p) for p in PoojaRepository(db).query_active().limit(HOME_POOJAS).all()],
    )


@router.get("/committee", response_model=List[CommitteeMemberPublic])
def committee(response: Response, db: Session = Depends(get_db)):
    """Members the temple chose to publish. Never includes phone or email."""
    response.headers["Cache-Control"] = "public, max-age=60"
    return MemberRepository(db).get_public()


# Only these site paths can be encoded, so this can never be used as a generic QR service.
QR_PATHS = {"/", "/register", "/login", "/poojas", "/abhishekam"}


@router.get("/qr")
def qr_code(path: str = "/"):
    """PNG QR code for a page on the temple's own site - shown on the lobby TV (/tv)
    so devotees can register, sign in or book a seva from their phone."""
    import io

    import qrcode
    from fastapi import HTTPException

    from app.core.config import settings

    if path not in QR_PATHS:
        raise HTTPException(status_code=400, detail="Unsupported path")
    buf = io.BytesIO()
    qrcode.make(settings.FRONTEND_BASE_URL.rstrip("/") + path, box_size=10, border=2).save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})
