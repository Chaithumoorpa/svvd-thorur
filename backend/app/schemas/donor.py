import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Optional

from pydantic import (
    BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator,
)

from app.models.finance import PaymentMode
from app.schemas.common import MoneyIn, MoneyOut, blank_to_none

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)]
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_PHONE_CHARS = set("0123456789+-() ")


class DonationType(str, Enum):
    GENERAL = "general"
    ANNADANAM = "annadanam"
    FESTIVAL = "festival"
    POOJA = "pooja"
    CONSTRUCTION = "construction"
    OTHER = "other"


def _check_phone(v):
    if v is None:
        return v
    digits = sum(ch.isdigit() for ch in v)
    if not (7 <= digits <= 15) or any(ch not in _PHONE_CHARS for ch in v):
        raise ValueError("Enter a valid phone number")
    return v


def _check_pan(v):
    if v is None:
        return v
    v = v.upper()
    if not _PAN_RE.match(v):
        raise ValueError("PAN must look like ABCDE1234F")
    return v


def mask_pan(pan: Optional[str]) -> Optional[str]:
    if not pan:
        return pan
    return f"{pan[:2]}{'*' * max(len(pan) - 3, 0)}{pan[-1]}"


# --------------------------------------------------------------------------- donors
class DonorBase(BaseModel):
    name: Name
    phone: Optional[str] = Field(default=None, max_length=32)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(default=None, max_length=1000)
    pan_number: Optional[str] = Field(default=None, max_length=20)

    @field_validator("phone", "email", "address", "pan_number", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return _check_phone(v)

    @field_validator("pan_number")
    @classmethod
    def _pan(cls, v):
        return _check_pan(v)


class DonorCreate(DonorBase):
    pass


class DonorUpdate(BaseModel):
    name: Optional[Name] = None
    phone: Optional[str] = Field(default=None, max_length=32)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(default=None, max_length=1000)
    pan_number: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None

    @field_validator("phone", "email", "address", "pan_number", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return _check_phone(v)

    @field_validator("pan_number")
    @classmethod
    def _pan(cls, v):
        return _check_pan(v)


class DonorOut(BaseModel):
    """Private donor record (TRUSTEE and above). PAN is masked unless the caller may write donors."""
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pan_number: Optional[str] = None
    is_active: bool
    donation_count: int = 0
    total_donated: MoneyOut = Decimal("0")
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------ donations
class DonationCreate(BaseModel):
    donor_id: int
    amount: MoneyIn
    donation_type: DonationType = DonationType.GENERAL
    purpose: Optional[str] = Field(default=None, max_length=1000)
    donated_on: Optional[datetime] = None
    payment_mode: PaymentMode = PaymentMode.CASH
    record_income: bool = Field(
        default=True, description="Also post this gift to the finance ledger as DONATION income"
    )

    @field_validator("purpose", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class DonationUpdate(BaseModel):
    amount: Optional[MoneyIn] = None
    donation_type: Optional[DonationType] = None
    purpose: Optional[str] = Field(default=None, max_length=1000)
    donated_on: Optional[datetime] = None
    payment_mode: Optional[PaymentMode] = None


class DonationOut(BaseModel):
    id: int
    donor_id: int
    donor_name: Optional[str] = None
    amount: MoneyOut
    donation_type: str
    purpose: Optional[str] = None
    donated_on: datetime
    payment_mode: PaymentMode
    receipt_number: Optional[str] = None
    receipt_generated_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
