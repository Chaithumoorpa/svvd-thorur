from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.models.base import Base


class Donor(Base):
    """
    Donor = Entity (someone who donated). PRIVATE data - never exposed publicly.
    Individual gifts live in `Donation`; the legacy per-donor amount columns
    still exist in old databases but are no longer mapped (see migration 003).
    """
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(32), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    pan_number = Column(String(20), nullable=True)  # For 80G tax receipts
    is_active = Column(Boolean, default=True, nullable=False)

    donations = relationship(
        "Donation", back_populates="donor", order_by="Donation.donated_on.desc()"
    )
