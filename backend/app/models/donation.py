from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
from app.models.finance import PaymentMode


class Donation(Base):
    """
    Donation entity - represents a single donation transaction.
    Linked to a Donor and optionally tracks who recorded it (User).
    """
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Link to donor
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False, index=True)
    
    # Donation details
    amount = Column(Integer, nullable=False)
    donation_type = Column(String(50), nullable=False, default="general")  # annadanam, festival, pooja, general, construction, other
    purpose = Column(Text, nullable=True)  # Specific purpose description
    donated_on = Column(DateTime, default=func.now(), nullable=False)
    
    # Receipt details
    receipt_number = Column(String(50), unique=True, nullable=True)
    receipt_generated_at = Column(DateTime, nullable=True)
    payment_mode = Column(SAEnum(PaymentMode), nullable=True, default=PaymentMode.CASH)
    
    # Audit: who recorded this donation in the system
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    donor = relationship("Donor", back_populates="donations")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])
