from sqlalchemy import Column, Integer, String, Time, Boolean
from app.models.base import Base


class TempleTiming(Base):
    """One row of the public darshan / opening schedule (e.g. 'Morning Darshan')."""
    __tablename__ = "temple_timings"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    days = Column(String(100), nullable=False, default="Daily")
    note = Column(String(300), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
