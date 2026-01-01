from sqlalchemy import Column, Integer, String, Date
from app.models.base import Base

class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(Integer, primary_key=True, index=True)
    ip_hash = Column(String, index=True, nullable=False)
    visit_date = Column(Date, index=True, nullable=False)
