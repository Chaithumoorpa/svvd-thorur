from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.models.occasion_blessing import BlessingPaymentStatus
from app.schemas.common import SafeUrl, blank_to_none, normalize_mobile

DevoteeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Occasion = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class OccasionBlessingCreate(BaseModel):
    """Public submission, gated on a verified email - see
    OtpService.request_occasion_otp/verify_occasion_otp. Price/payment are
    decided server-side, never client-supplied."""
    devotee_name: DevoteeName
    mobile_number: str
    email: EmailStr
    occasion: Occasion
    occasion_date: date
    relation: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = Field(default=None, max_length=500)
    photo_url: SafeUrl
    booking_token: str

    @field_validator("mobile_number")
    @classmethod
    def _mobile(cls, v):
        return normalize_mobile(v)

    @field_validator("relation", "message", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class OccasionBlessingOut(BaseModel):
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
    amount: Decimal
    payment_status: BlessingPaymentStatus
    paid_at: Optional[datetime] = None
    collected_by_admin_id: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class OccasionBlessingPublicOut(BaseModel):
    """The private page's own view - shape depends on `status`:
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
