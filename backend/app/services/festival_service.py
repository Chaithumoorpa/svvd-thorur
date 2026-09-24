from datetime import date
from typing import Optional

from fastapi import HTTPException

from app.models.festival import Festival
from app.repositories.festival_repo import FestivalRepository
from app.schemas.festival import FestivalCreate, FestivalUpdate


class FestivalService:
    def __init__(self, festival_repository: FestivalRepository):
        self.repo = festival_repository

    def list_active_festivals(self, upcoming_only: bool = False, limit: Optional[int] = None):
        return self.repo.get_all(date.today() if upcoming_only else None, limit)

    def query_all(self):
        return self.repo.query_all()

    def get_festival_details(self, festival_id: int, public: bool = True) -> Festival:
        festival = self.repo.get_by_id(festival_id)
        if not festival or (public and not festival.is_active):
            raise HTTPException(status_code=404, detail="Festival not found")
        return festival

    def create_festival(self, data: FestivalCreate) -> Festival:
        if self.repo.get_by_name(data.name):
            raise HTTPException(status_code=400, detail="Festival with this name already exists")
        return self.repo.create(Festival(**data.model_dump()))

    def update_festival(self, festival_id: int, data: FestivalUpdate) -> Festival:
        festival = self.get_festival_details(festival_id, public=False)
        fields = data.model_dump(exclude_unset=True)
        new_name = fields.get("name")
        if new_name and new_name != festival.name and self.repo.get_by_name(new_name):
            raise HTTPException(status_code=400, detail="Festival with this name already exists")
        for key, value in fields.items():
            if key in ("name", "festival_type", "is_active", "auto_announce", "announce_days_before") and value is None:
                continue
            setattr(festival, key, value)
        if festival.festival_date and festival.end_date and festival.end_date < festival.festival_date:
            raise HTTPException(status_code=422, detail="End date cannot be before the festival date")
        return self.repo.update(festival)

    def delete_festival(self, festival_id: int) -> Festival:
        """Soft delete."""
        festival = self.get_festival_details(festival_id, public=False)
        festival.is_active = False
        return self.repo.update(festival)
