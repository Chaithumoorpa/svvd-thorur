from app.repositories.festival_repo import FestivalRepository
from app.schemas.festival import FestivalCreate
from app.models.festival import Festival

from fastapi import HTTPException


class FestivalService:
    def __init__(self, festival_repository: FestivalRepository):
        self.festival_repository = festival_repository

    def list_active_festivals(self):
        """
        Returns all active festivals.
        Business rules can be added here later.
        """
        return self.festival_repository.get_all()

    def get_festival_details(self, festival_id: int):
        """
        Returns a single festival by id.
        """
        return self.festival_repository.get_by_id(festival_id)

    def create_festival(self, data: FestivalCreate):
        existing = self.festival_repository.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Festival with this name already exists"
            )

        festival = Festival(**data.dict())
        return self.festival_repository.create(festival)
