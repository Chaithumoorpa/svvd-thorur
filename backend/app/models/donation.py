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
    # S3 object key of the most recently archived receipt PDF (private bucket
    # prefix - contains donor name/address, never public like gallery photos).
    receipt_s3_key = Column(String, nullable=True)
    payment_mode = Column(SAEnum(PaymentMode), nullable=False, default=PaymentMode.CASH)

    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Optional: what this gift is for (a birthday, a wedding anniversary, ...).
    # Triggers a blessing email to the donor (if they have one on file) once
    # recorded - a donation is already "paid" the moment it's entered.
    occasion = Column(String(100), nullable=True)

    donor = relationship("Donor", back_populates="donations")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])
