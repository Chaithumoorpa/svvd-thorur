from sqlalchemy import Column, Integer, String, Date, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Announcement(Base):
    """
    Announcement = Public notices.
    Tracks who created it (User FK for audit).
    """
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
    
    # Audit: who created this announcement
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = relationship("User", back_populates="announcements")
