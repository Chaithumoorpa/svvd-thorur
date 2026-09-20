from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.utils.dependencies import get_db
from app.services.visitor_service import VisitorService
from app.schemas.visitor import VisitorStats
from app.utils.rate_limiter import get_client_ip

router = APIRouter()

@router.post("/track", status_code=200)
async def track_visitor(request: Request, db: Session = Depends(get_db)):
    # Get client IP
    client_ip = get_client_ip(request)

    VisitorService.track_visit(db, client_ip)
    return {"status": "tracked"}

@router.get("/stats", response_model=VisitorStats)
async def get_visitor_stats(db: Session = Depends(get_db)):
    return VisitorService.get_stats(db)
