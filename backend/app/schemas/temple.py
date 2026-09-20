from datetime import datetime, time
from typing import Annotated, List, Optional

from pydantic import (
    AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator,
    model_validator,
)

from app.schemas.common import OptionalSafeUrl, blank_to_none

Name150 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)]


class TempleUpdate(BaseModel):
    """Editable temple profile. Every field optional (PUT behaves like a partial update)."""
    name: Optional[Name150] = None
    deity_name: Optional[str] = Field(default=None, max_length=100)
    tagline: Optional[str] = Field(default=None, max_length=200)
    history: Optional[str] = Field(default=None, max_length=20000)
    address: Optional[str] = Field(default=None, max_length=300)
    village: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    pincode: Optional[str] = Field(default=None, max_length=10, pattern=r"^[0-9]{5,10}$|^$")
    map_url: OptionalSafeUrl = None
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    contact_email: Optional[EmailStr] = None
    whatsapp_number: Optional[str] = Field(default=None, max_length=20)
    hero_image_url: OptionalSafeUrl = None
    facebook_url: OptionalSafeUrl = None
    instagram_url: OptionalSafeUrl = None
    youtube_url: OptionalSafeUrl = None

    @model_validator(mode="before")
    @classmethod
    def _blank_strings(cls, data):
        if isinstance(data, dict):
            return {k: blank_to_none(v) for k, v in data.items()}
        return data


class TempleOut(BaseModel):
    """Everything here is intentionally public."""
    id: int
    name: str
    deity_name: Optional[str] = None
    tagline: Optional[str] = None
    history: Optional[str] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    map_url: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    whatsapp_number: Optional[str] = None
    hero_image_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    youtube_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TimingBase(BaseModel):
    label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    start_time: time
    end_time: time
    days: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] = "Daily"
    note: Optional[str] = Field(default=None, max_length=300)
    sort_order: int = Field(default=0, ge=0, le=1000)
    is_active: bool = True

    @model_validator(mode="after")
    def _order(self):
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        return self


class TimingCreate(TimingBase):
    pass


class TimingUpdate(BaseModel):
    label: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]] = None
    note: Optional[str] = Field(default=None, max_length=300)
    sort_order: Optional[int] = Field(default=None, ge=0, le=1000)
    is_active: Optional[bool] = None


class TimingOut(BaseModel):
    """Output model: no input validators, so stored rows always serialise."""
    id: int
    label: str
    start_time: time
    end_time: time
    days: str
    note: Optional[str] = None
    sort_order: int
    is_active: bool
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CommitteeMemberPublic(BaseModel):
    """Public committee entry - deliberately has NO phone/email."""
    id: int
    name: str
    position: Optional[str] = None
    photo_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
