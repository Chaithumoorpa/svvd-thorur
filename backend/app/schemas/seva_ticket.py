import re
from datetime import date, datetime, time
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.models.seva_ticket import PaymentStatus, TicketSource, TicketStatus
from app.schemas.common import MoneyInOrZero, MoneyOut

_MOBILE_RE = re.compile(r"^\+?[0-9]{10,14}$")
DevoteeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


def _mobile(v: str) -> str:
    v = re.sub(r"[\s-]", "", v)
    if not _MOBILE_RE.match(v):
        raise ValueError("Enter a valid mobile number (10-14 digits)")
    return v


class SevaBookingPublic(BaseModel):
    """
    Public online booking. The client can NOT set price, payment status or seva name -
    those are derived server-side from the pooja record.
    """
    seva_id: int
    devotee_name: DevoteeName
    mobile_number: str
    seva_date: date
    seva_time: Optional[time] = None

    @field_validator("mobile_number")
    @classmethod
    def _m(cls, v):
        return _mobile(v)


class SevaBookingOnline(SevaBookingPublic):
    """Public online booking, gated on a verified email: `booking_token` is the
    one issued by POST /seva-tickets/booking/verify-otp for this exact email."""
    email: EmailStr
    booking_token: str


class SevaTicketCreate(SevaBookingPublic):
    """Counter (staff) ticket: staff may record a fee and payment status."""
    seva_name: Optional[str] = Field(default=None, max_length=200)
    payment_status: PaymentStatus = PaymentStatus.FREE
    amount: MoneyInOrZero = 0


class SevaTicketOut(BaseModel):
    id: UUID
    ticket_number: str
    seva_id: int
    seva_name: str
    devotee_name: str
    mobile_number: str
    email: Optional[str] = None
    seva_date: date
    seva_time: Optional[time] = None
    payment_status: PaymentStatus
    amount: MoneyOut
    status: TicketStatus
    source: TicketSource
    created_by_admin_id: Optional[int] = None
    qr_token: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SevaTicketPrintData(BaseModel):
    """Formatted data for print template"""
    ticket_number: str
    seva_name: str
    devotee_name: str
    mobile_number: str
    seva_date: str  # Formatted as DD-MM-YYYY
    seva_time: Optional[str] = None  # Formatted as HH:MM AM/PM
    status: str
    qr_code_base64: str  # Base64 encoded QR code image
    temple_name: str = "Sri Varasiddhi Vinayaka Devasthanam"


class ScanRequest(BaseModel):
    """Request to scan a QR code"""
    qr_token: str


class ScanResponse(BaseModel):
    """Response after scanning a QR code"""
    success: bool
    message: str
    ticket: Optional[SevaTicketOut] = None


class SevaTicketFilter(BaseModel):
    """Query parameters for filtering tickets"""
    seva_id: Optional[int] = None
    seva_date: Optional[date] = None
    status: Optional[TicketStatus] = None
    mobile_number: Optional[str] = None
