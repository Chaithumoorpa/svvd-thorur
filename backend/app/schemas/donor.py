from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.finance import PaymentMode


class DonorBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    pan_number: Optional[str] = None


class DonorCreate(DonorBase):
    # Bounds match the donors table column sizes so oversize input is a 422, not a 500.
    name: str = Field(..., min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=32)
    email: Optional[str] = Field(default=None, max_length=200)
    pan_number: Optional[str] = Field(default=None, max_length=20)
    # These were missing, so DonorService.create_donor() raised AttributeError
    # (data.amount) and every "add donor" request returned HTTP 500.
    donated_for: Optional[str] = Field(default="general", max_length=100)
    amount: int = Field(..., le=100_000_000)  # > 0 is enforced in the service (HTTP 400)
    donated_on: Optional[datetime] = None
    payment_mode: PaymentMode = PaymentMode.CASH


class DonorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=32)
    email: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = None
    pan_number: Optional[str] = Field(default=None, max_length=20)
    donated_for: Optional[str] = Field(default=None, max_length=100)
    amount: Optional[int] = Field(default=None, le=100_000_000)
    donated_on: Optional[datetime] = None
    payment_mode: Optional[PaymentMode] = None
    is_active: Optional[bool] = None


class DonorOut(DonorBase):
    id: int
    donated_for: Optional[str] = None
    amount: int = 0
    donated_on: Optional[datetime] = None
    payment_mode: Optional[PaymentMode] = None
    receipt_number: Optional[str] = None
    receipt_generated_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
