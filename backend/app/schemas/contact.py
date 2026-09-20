from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.contact import ContactStatus

class ContactBase(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class ContactCreate(ContactBase):
    # Public, unauthenticated input: bound every field. Limits match the
    # contact_messages column sizes (name 100, email 100, subject 200); without
    # them an oversize value surfaces as a database error (HTTP 500).
    name: str = Field(..., min_length=1, max_length=100)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)

    @field_validator("email")
    @classmethod
    def email_fits_column(cls, v):
        if len(str(v)) > 100:
            raise ValueError("Email must be at most 100 characters")
        return v

class ContactUpdate(BaseModel):
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = Field(default=None, max_length=5000)

class ContactOut(ContactBase):
    id: int
    status: ContactStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
