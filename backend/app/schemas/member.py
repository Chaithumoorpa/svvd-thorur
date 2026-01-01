from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MemberBase(BaseModel):
    full_name: str
    designation: Optional[str] = None
    department: Optional[str] = None
    joining_date: Optional[datetime] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    is_active: bool = True


class MemberCreate(MemberBase):
    user_id: int


class MemberUpdate(BaseModel):
    full_name: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    joining_date: Optional[datetime] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    is_active: Optional[bool] = None


class MemberOut(MemberBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
