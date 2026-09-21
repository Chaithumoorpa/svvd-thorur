from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Numeric, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.models.base import Base
from app.models.types import MONEY_PRECISION, MONEY_SCALE


class PaymentStatus(str, enum.Enum):
    FREE = "FREE"
    PAID = "PAID"


class TicketStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    CANCELLED = "CANCELLED"


class TicketSource(str, enum.Enum):
    ONLINE = "ONLINE"
    COUNTER = "COUNTER"


class SevaTicket(Base):
    __tablename__ = "seva_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_number = Column(String, unique=True, nullable=False, index=True)
    
    # Seva details
    seva_id = Column(Integer, ForeignKey("poojas.id"), nullable=False)
    seva_name = Column(String, nullable=False)  # Denormalized for easier access
    
    # Devotee details
    devotee_name = Column(String, nullable=False)
    mobile_number = Column(String(15), nullable=False, index=True)
    
    # Schedule
    seva_date = Column(Date, nullable=False, index=True)
    seva_time = Column(Time, nullable=True)
    
    # Payment
    payment_status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.FREE)
    amount = Column(Numeric(MONEY_PRECISION, MONEY_SCALE), default=0, nullable=False)  # INR
    
    # Status & Security
    status = Column(SQLEnum(TicketStatus), nullable=False, default=TicketStatus.ACTIVE, index=True)
    source = Column(SQLEnum(TicketSource), nullable=False, default=TicketSource.ONLINE, index=True)
    created_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    qr_token = Column(String, unique=True, nullable=False, index=True)  # Secure random token

    # S3 object key of the most recently archived PDF (private bucket prefix,
    # contains devotee name/phone - never public like gallery photos).
    pdf_s3_key = Column(String, nullable=True)
