from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.contact import ContactStatus

class ContactBase(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    status: Optional[ContactStatus] = None
    admin_notes: Optional[str] = None

class ContactOut(ContactBase):
    id: int
    status: ContactStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
