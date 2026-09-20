from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base
from app.models.finance import PaymentMode
from app.models.types import MONEY_PRECISION, MONEY_SCALE


class Donation(Base):
    """
    A single donation. Linked to a Donor; records which user entered it.
    """
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False, index=True)

    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False)
    donation_type = Column(String(50), nullable=False, default="general")
    purpose = Column(Text, nullable=True)
    donated_on = Column(DateTime, default=func.now(), nullable=False, index=True)

    receipt_number = Column(String(50), unique=True, nullable=True)
    receipt_generated_at = Column(DateTime, nullable=True)
    payment_mode = Column(SAEnum(PaymentMode), nullable=False, default=PaymentMode.CASH)

    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    donor = relationship("Donor", back_populates="donations")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])
