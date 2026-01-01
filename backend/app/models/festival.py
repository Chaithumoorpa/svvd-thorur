from sqlalchemy import Column, Integer, String, Date, Boolean, Text
from app.models.base import Base

class Festival(Base):
    __tablename__ = "festivals"

    id = Column(Integer, primary_key=True, index=True)

    # Festival details
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # Timing
    festival_date = Column(Date, nullable=True)

    # Classification
    festival_type = Column(
        String(50),
        default="annual",
        nullable=False
    )
    # examples: annual, monthly, special

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
