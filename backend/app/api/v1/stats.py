from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.utils.dependencies import get_db
from app.utils.rate_limiter import visit_limiter, get_client_ip
from app.services.visitor_service import VisitorService
from app.schemas.visitor import VisitorStats

router = APIRouter()

@router.post("/track", status_code=200)
def track_visitor(request: Request, db: Session = Depends(get_db)):
    # get_client_ip() only honours X-Forwarded-For from the configured number of
    # trusted proxies. Reading the left-most entry (as this code used to) lets
    # anyone insert unlimited fake "unique visitors" by rotating that header.
    client_ip = get_client_ip(request)
    if not visit_limiter.is_allowed(client_ip):
        return {"status": "rate_limited"}

    VisitorService.track_visit(db, client_ip)
    return {"status": "tracked"}

@router.get("/stats", response_model=VisitorStats)
def get_visitor_stats(db: Session = Depends(get_db)):
    return VisitorService.get_stats(db)
