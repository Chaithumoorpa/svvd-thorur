from datetime import date, datetime, time
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator

from app.models.seva_ticket import PaymentStatus, TicketSource, TicketStatus
from app.schemas.common import MoneyInOrZero, MoneyOut, blank_to_none, normalize_mobile

# What POST /seva-tickets/booking/upload-url hands out - never an arbitrary URL,
# so a booking can only ever point at a photo uploaded to the private review prefix.
BLESSING_PHOTO_PREFIX = "blessings-pending"
PhotoKey = Annotated[str, StringConstraints(pattern=rf"^{BLESSING_PHOTO_PREFIX}/[0-9a-f]{{32}}\.(jpg|png|webp|gif)$")]

DevoteeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class SevaBookingPublic(BaseModel):
    """
    Public online booking. The client can NOT set price, payment status or seva name -
    those are derived server-side from the pooja record.
    """
    seva_id: int
    devotee_name: DevoteeName
    mobile_number: Annotated[str, StringConstraints(max_length=20)]
    seva_date: date
    seva_time: Optional[time] = None
    # What this booking is for (a birthday, a wedding anniversary, ...) - optional,
    # triggers a blessing email once the seva is paid for.
    occasion: Optional[str] = Field(default=None, max_length=100)

    @field_validator("mobile_number")
    @classmethod
    def _m(cls, v):
        return normalize_mobile(v)

    @field_validator("occasion", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class SevaBookingOnline(SevaBookingPublic):
    """Public online booking, gated on a verified email: `booking_token` is the
    one issued by POST /seva-tickets/booking/verify-otp for this exact email.
    `photo_key`/`show_publicly` only for a seva with public_blessings; both
    wait for staff review before anything appears on the website."""
    email: EmailStr
    booking_token: str = Field(max_length=2000)
    turnstile_token: Optional[str] = Field(default=None, max_length=4000)
    photo_key: Optional[PhotoKey] = None
    show_publicly: bool = False

    @model_validator(mode="after")
    def _blessing_needs_occasion(self):
        if (self.photo_key or self.show_publicly) and not self.occasion:
            raise ValueError("Add the occasion to share a blessing photo or show it publicly")
        return self


class SevaTicketCreate(SevaBookingPublic):
    """Counter (staff) ticket: staff may record a fee and payment status, and
    the devotee's email for their occasion blessing."""
    seva_name: Optional[str] = Field(default=None, max_length=200)
    payment_status: PaymentStatus = PaymentStatus.FREE
    amount: MoneyInOrZero = 0
    email: Optional[EmailStr] = None

    @field_validator("email", mode="before")
    @classmethod
    def _blank_email(cls, v):
        return blank_to_none(v)


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
    occasion: Optional[str] = None
    photo_url: Optional[str] = None
    review_status: Optional[str] = None
    show_publicly: bool = False
    status: TicketStatus
    source: TicketSource
    created_by_admin_id: Optional[int] = None
    booked_by_user_id: Optional[int] = None
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
    temple_name: str = "Sri Varasidhi Vinayaka Devasthanam"


class ScanRequest(BaseModel):
    """Request to scan a QR code"""
    qr_token: str = Field(max_length=200)


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
