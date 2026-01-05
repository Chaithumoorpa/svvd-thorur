from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DonorBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pan_number: Optional[str] = None


class DonorCreate(DonorBase):
    pass


class DonorUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pan_number: Optional[str] = None
    is_active: Optional[bool] = None


class DonorOut(DonorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
