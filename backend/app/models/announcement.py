from sqlalchemy import Column, Integer, String, Date, Boolean, Text
from app.models.base import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)

    # Visibility window
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
