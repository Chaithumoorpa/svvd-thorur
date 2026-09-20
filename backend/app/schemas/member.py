from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.schemas.common import OptionalSafeUrl, blank_to_none

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
_PHONE_CHARS = set("0123456789+-() ")


def _check_phone(value: str) -> str:
    value = value.strip()
    digits = sum(ch.isdigit() for ch in value)
    if not (7 <= digits <= 15) or any(ch not in _PHONE_CHARS for ch in value):
        raise ValueError("Enter a valid phone number")
    return value


class MemberBase(BaseModel):
    name: Name
    phone: str
    email: Optional[EmailStr] = None
    position: Optional[str] = Field(default=None, max_length=100)  # Trustee, Priest, Staff...
    show_on_website: bool = False
    sort_order: int = Field(default=0, ge=0, le=10000)
    photo_url: OptionalSafeUrl = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return _check_phone(v)

    @field_validator("email", "position", "photo_url", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[Name] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    position: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None
    show_on_website: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0, le=10000)
    photo_url: OptionalSafeUrl = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return _check_phone(v) if v is not None else v

    @field_validator("email", "position", "photo_url", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class MemberOut(BaseModel):
    """Admin/trustee view (includes private contact details). No input validators:
    legacy rows must always be serialisable."""
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    position: Optional[str] = None
    show_on_website: bool
    sort_order: int
    photo_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
