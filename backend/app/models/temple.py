from sqlalchemy import Column, Integer, String, Text, Boolean
from app.models.base import Base

class Temple(Base):
    __tablename__ = "temples"

    id = Column(Integer, primary_key=True, index=True)

    # Basic identity
    name = Column(String(150), nullable=False)
    deity_name = Column(String(100), nullable=True)

    # Description / history
    history = Column(Text, nullable=True)

    # Location details
    village = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)

    # Contact info (public)
    contact_phone = Column(String(20), nullable=True)
    contact_email = Column(String(100), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
