from datetime import date, datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


def _check_window(start: Optional[date], end: Optional[date]) -> None:
    if start and end and end < start:
        raise ValueError("End date cannot be before start date")


class AnnouncementCreate(BaseModel):
    title: Title
    message: Optional[str] = Field(default=None, max_length=5000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def _window(self):
        _check_window(self.start_date, self.end_date)
        return self


class AnnouncementUpdate(BaseModel):
    title: Optional[Title] = None
    message: Optional[str] = Field(default=None, max_length=5000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def _window(self):
        _check_window(self.start_date, self.end_date)
        return self


class AnnouncementOut(BaseModel):
    id: int
    title: str
    message: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    source_festival_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
