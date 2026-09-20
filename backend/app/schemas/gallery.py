from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.schemas.common import SafeUrl, blank_to_none

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Category = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=2, max_length=50)]


class GalleryCreate(BaseModel):
    title: Title
    description: Optional[str] = Field(default=None, max_length=2000)
    image_url: SafeUrl
    category: Category = "TEMPLE"
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=10000)

    @field_validator("description", mode="before")
    @classmethod
    def _blank(cls, v):
        return blank_to_none(v)


class GalleryUpdate(BaseModel):
    title: Optional[Title] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    image_url: Optional[SafeUrl] = None
    category: Optional[Category] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(default=None, ge=0, le=10000)


class GalleryOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image_url: str
    category: str
    is_active: bool
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
