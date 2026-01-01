from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.visitor import VisitorLog

class VisitorRepo:
    @staticmethod
    def get_or_create_visit(db: Session, ip_hash: str, visit_date: date) -> VisitorLog:
        visit = db.query(VisitorLog).filter(
            VisitorLog.ip_hash == ip_hash,
            VisitorLog.visit_date == visit_date
        ).first()
        
        if not visit:
            visit = VisitorLog(ip_hash=ip_hash, visit_date=visit_date)
            db.add(visit)
            db.commit()
            db.refresh(visit)
        return visit

    @staticmethod
    def get_total_count(db: Session) -> int:
        return db.query(func.count(VisitorLog.id)).scalar() or 0

    @staticmethod
    def get_today_count(db: Session) -> int:
        return db.query(func.count(VisitorLog.id)).filter(
            VisitorLog.visit_date == date.today()
        ).scalar() or 0
