from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.models.contact import ContactStatus

Str = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ContactCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
    email: EmailStr
    subject: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=5000)]
    # Honeypot: real visitors never see/fill this hidden field, bots usually do.
    website: Optional[str] = Field(default=None, max_length=200, exclude=True)


class ContactUpdate(BaseModel):
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = Field(default=None, max_length=5000)


class ContactPublicAck(BaseModel):
    """What the public form receives back - never the stored message/notes."""
    id: int
    status: ContactStatus
    model_config = ConfigDict(from_attributes=True)


class ContactOut(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    status: ContactStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
