from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class FestivalBase(BaseModel):
    name: str
    description: Optional[str] = None
    festival_date: Optional[date] = None
    festival_type: str
    is_active: bool


class FestivalCreate(BaseModel):
    name: str
    description: Optional[str] = None
    festival_date: Optional[date] = None
    festival_type: str = "annual"


class FestivalOut(FestivalBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
