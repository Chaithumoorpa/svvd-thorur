from pydantic import BaseModel
from typing import Optional
from datetime import time, datetime

class PoojaBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    pooja_type: str
    is_paid: bool
    suggested_amount: Optional[int] = None
    is_active: bool

class PoojaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    pooja_type: str = "daily"
    is_paid: bool = False
    suggested_amount: Optional[int] = None

class PoojaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    pooja_type: Optional[str] = None
    is_paid: Optional[bool] = None
    suggested_amount: Optional[int] = None
    is_active: Optional[bool] = None

class PoojaOut(PoojaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (SQLAlchemy -> schema)
