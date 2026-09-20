import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date, time
from uuid import UUID

from app.models.seva_ticket import PaymentStatus, TicketStatus, TicketSource


class SevaTicketBase(BaseModel):
    seva_id: int
    seva_name: str
    devotee_name: str
    mobile_number: str = Field(..., min_length=10, max_length=15)
    seva_date: date
    seva_time: Optional[time] = None
    payment_status: PaymentStatus = PaymentStatus.FREE
    amount: int = 0


class SevaTicketCreate(SevaTicketBase):
    """
    Schema for creating a new seva ticket.

    Used by the public booking endpoint, so every field is bounded. Note that the
    public endpoint ignores `payment_status` and `amount` (a visitor must not be
    able to mint a ticket that prints as PAID); only counter tickets created by
    an admin keep them.
    """
    seva_name: Optional[str] = Field(default=None, max_length=150)  # server uses the pooja's own name
    devotee_name: str = Field(..., min_length=1, max_length=150)
    mobile_number: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    amount: int = Field(default=0, ge=0, le=1_000_000)

    @field_validator("mobile_number", mode="before")
    @classmethod
    def strip_phone_separators(cls, v):
        """Accept '98765 43210' or '98765-43210' as typed at the counter."""
        return re.sub(r"[\s\-()]", "", v) if isinstance(v, str) else v


class SevaTicketOut(SevaTicketBase):
    """Schema for returning seva ticket details"""
    id: UUID
    ticket_number: str
    status: TicketStatus
    source: TicketSource
    created_by_admin_id: Optional[int] = None
    qr_token: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
    temple_name: str = "Sri Varasiddi Vinayaka Devasthanam"


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
