"""Order-then-confirm payment flows over Razorpay - see razorpay_service.py's
docstring for the shape. `payment_token` carries the validated request
(seva booking fields, or donor+donation fields) from the order step to the
confirm step as a signed JWT; nothing is written to the database until the
payment is verified."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.finance import PaymentMode
from app.schemas.common import blank_to_none, normalize_mobile
from app.schemas.donor import DonationType, _check_pan
from app.schemas.seva_ticket import SevaBookingOnline

MAX_ONLINE_AMOUNT = 1_000_000  # rupees - matches the donation form's own bound


class RazorpayOrderOut(BaseModel):
    order_id: str
    amount_paise: int
    currency: str
    key_id: str  # public key - safe to expose to the client, needed by Razorpay's Checkout.js
    payment_token: str


class RazorpayConfirmIn(BaseModel):
    payment_token: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentStatusOut(BaseModel):
    """Public: whether online payment is set up, so the UI can show the real
    form or fall back to the offline path without a failed request first."""
    enabled: bool


# ---------------------------------------------------------------- paid seva booking
class SevaPaymentOrderIn(SevaBookingOnline):
    """Same booking request as the free/offline path (POST /seva-tickets) -
    OTP-verified email, optional occasion/blessing photo - for a seva that
    has a fee. The amount itself is never taken from here; it's the seva's
    own suggested_amount at order time (and re-read at confirm time)."""


# ------------------------------------------------------------------- donation
class DonationOrderIn(BaseModel):
    """A public donation, before payment. Unlike the admin-recorded donation
    (POST /donations/, which requires an existing donor_id and staff auth),
    this finds or creates the donor by phone once payment is verified."""
    donor_name: str = Field(min_length=2, max_length=150)
    # Normalized the same way as a seva booking's mobile number, so a repeat
    # donor is matched to their existing donor record (see
    # DonationService.find_or_create_donor_by_phone) instead of a lookalike
    # new one every time.
    phone: str = Field(max_length=32)
    email: Optional[EmailStr] = None
    pan_number: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=1000)
    amount: float = Field(gt=0, le=MAX_ONLINE_AMOUNT)
    donation_type: DonationType = DonationType.GENERAL
    purpose: Optional[str] = Field(default=None, max_length=1000)
    occasion: Optional[str] = Field(default=None, max_length=100)
    turnstile_token: Optional[str] = None

    @field_validator("email", "pan_number", "address", "purpose", "occasion", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return normalize_mobile(v)

    @field_validator("pan_number")
    @classmethod
    def _pan(cls, v):
        return _check_pan(v)


# The payment_mode this flow always records - never taken from the client.
DONATION_ONLINE_MODE = PaymentMode.ONLINE
