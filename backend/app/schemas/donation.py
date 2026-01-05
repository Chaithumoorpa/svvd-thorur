from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.finance import PaymentMode


class DonationBase(BaseModel):
    donor_id: int
    amount: int
    donation_type: str = "general"  # annadanam, festival, pooja, general, construction, other
    purpose: Optional[str] = None
    donated_on: Optional[datetime] = None
    payment_mode: Optional[PaymentMode] = PaymentMode.CASH


class DonationCreate(DonationBase):
    pass


class DonationUpdate(BaseModel):
    amount: Optional[int] = None
    donation_type: Optional[str] = None
    purpose: Optional[str] = None
    donated_on: Optional[datetime] = None
    payment_mode: Optional[PaymentMode] = None
    receipt_number: Optional[str] = None


class DonationOut(BaseModel):
    id: int
    donor_id: int
    amount: int
    donation_type: str
    purpose: Optional[str] = None
    donated_on: datetime
    receipt_number: Optional[str] = None
    receipt_generated_at: Optional[datetime] = None
    payment_mode: Optional[PaymentMode] = None
    recorded_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
