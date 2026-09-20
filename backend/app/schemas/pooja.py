from datetime import datetime, time
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.schemas.common import MoneyInOrZero, MoneyOut, blank_to_none

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]
Money = MoneyInOrZero


class PoojaCreate(BaseModel):
    name: Name
    description: Optional[str] = Field(default=None, max_length=3000)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    pooja_type: str = Field(default="daily", max_length=50)
    is_paid: bool = False
    suggested_amount: Optional[Money] = None
    sort_order: int = Field(default=0, ge=0, le=10000)

    @field_validator("description", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)

    @model_validator(mode="after")
    def _rules(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        if self.is_paid and self.suggested_amount is None:
            raise ValueError("A paid seva needs an amount")
        return self


class PoojaUpdate(BaseModel):
    name: Optional[Name] = None
    description: Optional[str] = Field(default=None, max_length=3000)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    pooja_type: Optional[str] = Field(default=None, max_length=50)
    is_paid: Optional[bool] = None
    suggested_amount: Optional[Money] = None
    sort_order: Optional[int] = Field(default=None, ge=0, le=10000)
    is_active: Optional[bool] = None

    @field_validator("description", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class PoojaOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    pooja_type: str
    is_paid: bool
    suggested_amount: Optional[MoneyOut] = None
    sort_order: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
