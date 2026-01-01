from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from app.models.base import Base
from app.models.finance import PaymentMode


class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    phone = Column(String(32), nullable=True)
    email = Column(String(200), nullable=True)
    donated_for = Column(String(100), nullable=True)  # annadanam, festival, pooja, general
    amount = Column(Integer, nullable=False)
    donated_on = Column(DateTime, default=func.now(), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    
    # Receipt Fields
    receipt_number = Column(String(50), unique=True, nullable=True)
    receipt_generated_at = Column(DateTime, nullable=True)
    payment_mode = Column(Enum(PaymentMode), nullable=True, default=PaymentMode.CASH)
