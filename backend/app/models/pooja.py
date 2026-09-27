from sqlalchemy import Column, Integer, String, Time, Boolean, Text, Numeric
from app.models.base import Base
from app.models.types import MONEY_PRECISION, MONEY_SCALE

class Pooja(Base):
    __tablename__ = "poojas"

    id = Column(Integer, primary_key=True, index=True)

    # Core info
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Timing
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    # Classification
    pooja_type = Column(
        String(50),
        nullable=False,
        default="daily"
    )  
    # examples: daily, weekly, monthly, festival, special

    # Optional donation / seva info (future-ready)
    is_paid = Column(Boolean, default=False, nullable=False)
    suggested_amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=True)  # INR
    sort_order = Column(Integer, default=0, nullable=False)

    # Bookings allowed per date, online and counter alike (cancelled ones free
    # their slot); None = unlimited. 7 for Abhishekam, like the paper register.
    daily_slot_cap = Column(Integer, nullable=True)
    # Devotees booking this seva may add one occasion photo and show their
    # blessing publicly - the Abhishekam calendar and blessings pages.
    public_blessings = Column(Boolean, default=False, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
