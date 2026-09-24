from datetime import date, datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.schemas.common import OptionalSafeUrl, blank_to_none

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=150)]


class FestivalCreate(BaseModel):
    name: Name
    description: Optional[str] = Field(default=None, max_length=5000)
    festival_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = Field(default=None, max_length=200)
    image_url: OptionalSafeUrl = None
    festival_type: str = Field(default="annual", max_length=50)
    auto_announce: bool = True
    announce_days_before: int = Field(default=2, ge=0, le=30)

    @field_validator("location", "image_url", "description", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @model_validator(mode="after")
    def _window(self):
        if self.festival_date and self.end_date and self.end_date < self.festival_date:
            raise ValueError("End date cannot be before the festival date")
        return self


class FestivalUpdate(BaseModel):
    name: Optional[Name] = None
    description: Optional[str] = Field(default=None, max_length=5000)
    festival_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = Field(default=None, max_length=200)
    image_url: OptionalSafeUrl = None
    festival_type: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    auto_announce: Optional[bool] = None
    announce_days_before: Optional[int] = Field(default=None, ge=0, le=30)

    @field_validator("location", "image_url", "description", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class FestivalOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    festival_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    festival_type: str
    is_active: bool
    auto_announce: bool
    announce_days_before: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
