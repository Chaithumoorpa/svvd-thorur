import enum
import uuid

from sqlalchemy import (
    Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base
from app.models.types import MONEY_PRECISION, MONEY_SCALE

BLESSING_FEE = 50  # fixed price in INR - never client-supplied, see the schema/service
BLESSING_VISIBILITY_DAYS = 7


class BlessingPaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"


class OccasionBlessing(Base):
    """A devotee's paid 'Occasion Blessing' page: an uploaded photo plus an
    occasion (birthday, wedding anniversary, ...), shown at a private link
    for BLESSING_VISIBILITY_DAYS once the temple has collected the fee.
    Payment is pay-at-counter, the same PENDING/PAID pattern as a paid seva
    ticket booked online - see collect_payment in the service."""
    __tablename__ = "occasion_blessings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    reference_number = Column(String, unique=True, nullable=False, index=True)

    devotee_name = Column(String, nullable=False)
    mobile_number = Column(String(15), nullable=False, index=True)
    email = Column(String(255), nullable=False)

    occasion = Column(String(100), nullable=False)
    occasion_date = Column(Date, nullable=False)
    relation = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    photo_url = Column(String, nullable=False)

    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), nullable=False, default=BLESSING_FEE)
    payment_status = Column(SQLEnum(BlessingPaymentStatus), nullable=False, default=BlessingPaymentStatus.PENDING)
    paid_at = Column(DateTime, nullable=True)
    collected_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # created_at/updated_at are inherited from Base.
