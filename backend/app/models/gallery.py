from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from app.models.base import Base

class Gallery(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=False)
    category = Column(String, nullable=False) # TEMPLE, FESTIVAL, EVENT
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
