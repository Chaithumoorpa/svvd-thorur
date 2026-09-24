from sqlalchemy import Column, Integer, String, Date, Boolean, Text
from app.models.base import Base


class Festival(Base):
    __tablename__ = "festivals"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)

    # festival_date is the first day; end_date is optional for multi-day events
    festival_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    location = Column(String(200), nullable=True)
    image_url = Column(String(500), nullable=True)

    # examples: annual, monthly, special
    festival_type = Column(String(50), default="annual", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    # A daily job (see app/cli/generate_festival_announcements.py) creates one
    # Announcement per festival, `announce_days_before` days ahead of festival_date.
    auto_announce = Column(Boolean, default=True, nullable=False)
    announce_days_before = Column(Integer, default=2, nullable=False)
