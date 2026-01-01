import hashlib
from datetime import date
from sqlalchemy.orm import Session
from app.repositories.visitor_repo import VisitorRepo
from app.core.config import SECRET_KEY

class VisitorService:
    @staticmethod
    def track_visit(db: Session, ip_address: str):
        # Hash IP address with salt for privacy
        ip_hash = hashlib.sha256(f"{ip_address}{SECRET_KEY}".encode()).hexdigest()
        today = date.today()
        return VisitorRepo.get_or_create_visit(db, ip_hash, today)

    @staticmethod
    def get_stats(db: Session):
        return {
            "total_visitors": VisitorRepo.get_total_count(db),
            "today_visitors": VisitorRepo.get_today_count(db)
        }
