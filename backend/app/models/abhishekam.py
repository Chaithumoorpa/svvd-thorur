import enum
import uuid

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.types import MONEY_PRECISION, MONEY_SCALE

ABHISHEKAM_FEE = 50  # fixed price in INR - never client-supplied, see the schema/service
ABHISHEKAM_VISIBILITY_DAYS = 7  # how long the devotee's own dedicated page stays up
DAILY_SLOT_CAP = 7  # only this many Abhishekam bookings per calendar date


class AbhishekamPaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"


class AbhishekamVisibility(str, enum.Enum):
    """The devotee's choice at booking time. PUBLIC entries appear (name,
    occasion, photo) on the public yearly calendar's day flyer; PRIVATE ones
    never do - but every booking still counts toward that date's
    DAILY_SLOT_CAP and still gets its own dedicated page + greeting email,
    regardless of visibility."""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class Abhishekam(Base):
    """A devotee's paid Abhishekam booking for a specific date - capped at
    DAILY_SLOT_CAP per date, like the temple's paper register (see the photo
    that prompted this feature). Optionally tied to a personal occasion
    (birthday, wedding anniversary, ...) with an uploaded photo, shown at a
    private link for ABHISHEKAM_VISIBILITY_DAYS once the temple has collected
    the fee. Payment is pay-at-counter, the same PENDING/PAID pattern as a
    paid seva ticket booked online - see collect_payment in the service."""
    __tablename__ = "abhishekams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    reference_number = Column(String, unique=True, nullable=False, index=True)

    devotee_name = Column(String, nullable=False)
    mobile_number = Column(String(15), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    occasion = Column(String(100), nullable=False)
    occasion_date = Column(Date, nullable=False, index=True)  # the Abhishekam's own date - counts toward DAILY_SLOT_CAP
    relation = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    photo_url = Column(String, nullable=False)
    visibility = Column(
        SQLEnum(AbhishekamVisibility, name="abhishekamvisibility"),
        nullable=False, default=AbhishekamVisibility.PRIVATE,
    )

    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False, default=ABHISHEKAM_FEE)
    payment_status = Column(
        SQLEnum(AbhishekamPaymentStatus, name="abhishekampaymentstatus"),
        nullable=False, default=AbhishekamPaymentStatus.PENDING,
    )
    paid_at = Column(DateTime, nullable=True)
    collected_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # created_at/updated_at are inherited from Base.
