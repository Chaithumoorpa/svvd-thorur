from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DonorCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    donated_for: Optional[str] = "general"
    amount: int
    donated_on: Optional[datetime] = None


class DonorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    donated_for: Optional[str] = None
    amount: Optional[int] = None
    donated_on: Optional[datetime] = None
    is_active: Optional[bool] = None


class DonorOut(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    donated_for: Optional[str] = None
    amount: int
    donated_on: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
