from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MemberBase(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    position: Optional[str] = None  # e.g., Trustee, Priest, Staff


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


class MemberOut(MemberBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
