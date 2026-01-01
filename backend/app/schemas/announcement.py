from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class AnnouncementCreate(BaseModel):
    title: str
    message: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class AnnouncementOut(BaseModel):
    id: int
    title: str
    message: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
