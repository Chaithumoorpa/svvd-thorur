from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.models.abhishekam import AbhishekamPaymentStatus, AbhishekamVisibility
from app.schemas.common import SafeUrl, blank_to_none, normalize_mobile

DevoteeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Occasion = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class AbhishekamCreate(BaseModel):
    """Public submission, gated on a verified email - see
    OtpService.request_abhishekam_otp/verify_abhishekam_otp. Price/payment
    are decided server-side, never client-supplied. `occasion_date` is the
    Abhishekam's own date - capped at DAILY_SLOT_CAP bookings per date."""
    devotee_name: DevoteeName
    mobile_number: str
    email: EmailStr
    occasion: Occasion
    occasion_date: date
    relation: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = Field(default=None, max_length=500)
    photo_url: SafeUrl
    visibility: AbhishekamVisibility = AbhishekamVisibility.PRIVATE
    booking_token: str

    @field_validator("mobile_number")
    @classmethod
    def _mobile(cls, v):
        return normalize_mobile(v)

    @field_validator("relation", "message", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class AbhishekamOut(BaseModel):
    """Admin/staff view - every field, for the counter-collection list."""
    id: UUID
    reference_number: str
    devotee_name: str
    mobile_number: str
    email: str
    occasion: str
    occasion_date: date
    relation: Optional[str] = None
    message: Optional[str] = None
    photo_url: str
    visibility: AbhishekamVisibility
    amount: Decimal
    payment_status: AbhishekamPaymentStatus
    paid_at: Optional[datetime] = None
    collected_by_admin_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AbhishekamPersonalPageOut(BaseModel):
    """The devotee's own dedicated link - shape depends on `status`:
    - pending: occasion/reference only, nothing paid-for yet.
    - active: everything, plus `expires_at` so the page can show a countdown.
    - expired: same as pending - the 7-day window has passed."""
    status: Literal["pending", "active", "expired"]
    reference_number: str
    occasion: str
    occasion_date: date
    devotee_name: Optional[str] = None
    relation: Optional[str] = None
    message: Optional[str] = None
    photo_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class AbhishekamCalendarDay(BaseModel):
    """One day's slot usage for the public 365-day calendar grid."""
    date: date
    slots_used: int
    slots_total: int


class AbhishekamDayEntry(BaseModel):
    """One PUBLIC, PAID booking shown on a day's flyer - never a PENDING or
    PRIVATE one, see AbhishekamService.day_flyer."""
    devotee_name: str
    occasion: str
    photo_url: str


class AbhishekamDayFlyer(BaseModel):
    date: date
    slots_used: int
    slots_total: int
    entries: List[AbhishekamDayEntry]
