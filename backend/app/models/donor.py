from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.sql import func
from app.models.base import Base
from app.models.finance import PaymentMode


class Donor(Base):
    """
    Donor = Entity (someone who donated).
    Standalone - donors typically don't have accounts.

    A donation is stored on the donor row ("kept in donor for simplicity"), which is
    what the API and admin UI use. The receipt fields below were referenced by the
    receipt endpoints and PDF service but were never defined, so generating or
    downloading a receipt failed.
    """
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(32), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    pan_number = Column(String(20), nullable=True)  # For 80G tax receipts

    # Donation details (kept in donor for simplicity)
    donated_for = Column(String(100), nullable=True)  # annadanam, festival, pooja, general
    amount = Column(Integer, nullable=False, default=0)
    donated_on = Column(DateTime, default=func.now(), nullable=False)
    payment_mode = Column(SAEnum(PaymentMode), nullable=False, default=PaymentMode.CASH)

    # Receipt (assigned when an admin generates it)
    receipt_number = Column(String(50), unique=True, nullable=True)
    receipt_generated_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
