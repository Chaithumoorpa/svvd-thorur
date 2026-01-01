from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.utils.dependencies import get_db
from app.services.visitor_service import VisitorService
from app.schemas.visitor import VisitorStats

router = APIRouter()

@router.post("/track", status_code=200)
async def track_visitor(request: Request, db: Session = Depends(get_db)):
    # Get client IP
    client_ip = request.client.host
    # Forwarded for header check if behind proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0]
        
    VisitorService.track_visit(db, client_ip)
    return {"status": "tracked"}

@router.get("/stats", response_model=VisitorStats)
async def get_visitor_stats(db: Session = Depends(get_db)):
    return VisitorService.get_stats(db)
